# coding=utf-8
import codecs
import locale
import os
import random
import re
from nltk.classify import NaiveBayesClassifier, PositiveNaiveBayesClassifier
from nltk.tokenize import word_tokenize, RegexpTokenizer
from reader.models import ReaderUser, Entry, ReadEntry, ReceivedEntry, Feed

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

all_title_words = set()
all_description_words = set()
tokenizer = RegexpTokenizer(r'\w+-\w+|[a-zA-Z]\w+|\d+[a-zA-Z]+',
                            flags=re.UNICODE|re.MULTILINE)

def remove_stopwords(words):
    this_dir = os.path.dirname(__file__)
    stopwords = None

    with codecs.open(os.path.join(this_dir,
                                  'documents',
                                  'stopwords.txt'),
                     'r', encoding='utf-8') as stopwords_file:
        stopwords = tokenizer.tokenize(stopwords_file.read(stopwords_file))
    
    non_stopwords = set()
    for w in words:
        if w.lower() not in stopwords:
            non_stopwords.add(w.lower())

    return non_stopwords


def remove_html_tags(text):
    result = ' '.join(re.split(r'<.*>', text, 0,
                               re.UNICODE | re.DOTALL))
    return result


def slugify(text):
    new_text = remove_html_tags(text)

    return ' '.join(re.split(r'\s\d+|\W\s', new_text, 0,
                             re.UNICODE))

def get_word_features(user):
    received_entries = ReceivedEntry.objects.filter(reader_user=user)
    
    for r in received_entries:
        all_title_words.update(remove_stopwords(
                tokenizer.tokenize(r.entry.title)))
        
        slug_description = slugify(r.entry.description)
        all_description_words.update(
            remove_stopwords(tokenizer.tokenize(slug_description)))

    print all_title_words
    print all_description_words


def extract_features(entry):
    features = dict()
    title_words = remove_stopwords(tokenizer.tokenize(entry.title))
    
    slug_description = slugify(entry.description)
    description_words = remove_stopwords(tokenizer.tokenize(slug_description))
    feed = entry.feed

    for word in all_title_words:
        features['title_contains(%s)' % word] = (word in title_words)
    for word in all_description_words:
        features['description_contains(%s)' % word] = (word in description_words)
    features['from_feed'] = feed
    return features


def train_nb(user, feed=None):
    get_word_features(user)

    if (feed == None):
        shown_receipts = ReceivedEntries.objects.filter(
            reader_user=user,
            showed_to_user=True).order_by('-entry__pub_date')[:200]
        user_entries_read = [
            r.entry
            for r in ReadEntries.objects.filter(reader_user=user)]
    else:
        shown_receipts = ReceivedEntry.objects.filter(
            reader_user=user,
            entry__feed=feed,
            showed_to_user=True).order_by('-entry__pub_date')[:200]
        user_entries_read = [
            r.entry
            for r in ReadEntry.objects.filter(entry__feed=feed,
                                              reader_user=user)]

    sample_size = 15 if len(shown_receipts) >= 100 else len(user_entries_read)
    read_sample = random.sample(user_entries_read, sample_size)
    unread_entries = [r.entry for r in shown_receipts if r.entry not in user_entries_read]
    unread_sample = random.sample(unread_entries, sample_size)
    user_featureset = []
    
    for e in read_sample:
        user_featureset.append((extract_features(e), 'interesting'))
    for e in unread_sample:
        user_featureset.append((extract_features(e), 'not_interesting'))

    return NaiveBayesClassifier.train(user_featureset)


def train_positivenb(user, feed=None):
    get_word_features(user)

    if (feed == None):
        shown_receipts = ReceivedEntries.objects.filter(
            reader_user=user,
            showed_to_user=True).order_by('-entry__pub_date')[:200]
        user_entries_read = [
            r.entry
            for r in ReadEntries.objects.filter(reader_user=user)]
    else:
        shown_receipts = ReceivedEntry.objects.filter(
            reader_user=user,
            entry__feed=feed,
            showed_to_user=True).order_by('-entry__pub_date')[:200]
        user_entries_read = [
            r.entry
            for r in ReadEntry.objects.filter(entry__feed=feed,
                                              reader_user=user)]

    sample_size = 15 if len(shown_receipts) >= 100 else len(user_entries_read)
    read_sample = random.sample(user_entries_read, sample_size)
    unread_entries = [r.entry for r in shown_receipts if r.entry not in user_entries_read]
    if not unread_entries:
        unread_entries = ReceivedEntry.objects.filter(
            reader_user=user).exclude(id__in=[r.id for r in user_entries_read]).order_by('-entry__pub_date')[:200]
        unread_entries = [r.entry for r in unread_entries]
    unread_sample = random.sample(unread_entries, sample_size*3)
    read_featureset = [extract_features(e) for e in read_sample]
    unread_featureset = [extract_features(e) for e in unread_sample]

    return PositiveNaiveBayesClassifier.train(read_featureset, unread_featureset)


def classify(entry, classifier):
    features = extract_features(entry)
    return classifier.classify(features)
