# coding=utf-8
import codecs
import locale
import os
import random
import re
from nltk.classify import PositiveNaiveBayesClassifier, accuracy #NaiveBayesClassifier
from reader.naive_bayes import NaiveBayesClassifier
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize, RegexpTokenizer
from reader.models import ReaderUser, Entry, ReadEntry, ReceivedEntry, Feed

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

title_features = None
description_features = None
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
    global title_features, description_features

    received_entries = ReceivedEntry.objects.filter(reader_user=user)
    all_title_words = []
    all_description_words = []
    for r in received_entries:
        all_title_words.extend(
            remove_stopwords(tokenizer.tokenize(r.entry.title)))
        
        slug_description = slugify(r.entry.description)
        all_description_words.extend(
            remove_stopwords(tokenizer.tokenize(slug_description)))

    title_features = FreqDist(w for w in all_title_words).keys()[:2000]
    description_features = FreqDist(w for w in all_description_words).keys()[:2000]


def extract_features(entry):
    features = []
    title_words = remove_stopwords(tokenizer.tokenize(entry.title))
    
    slug_description = slugify(entry.description)
    description_words = remove_stopwords(tokenizer.tokenize(slug_description))
    feed = entry.feed

    features.extend(title_words)
    features.extend(description_words)

    return features


def train_nb(user, to_be_shown, feed=None):
    get_word_features(user)

    #if (feed == None):
    shown_receipts = ReceivedEntry.objects.filter(
        reader_user=user,
        showed_to_user=True)
    '''
    else:
        shown_receipts = ReceivedEntry.objects.filter(
        reader_user=user,
            entry__feed=feed,
            showed_to_user=True)
    '''
    read_entries = ReadEntry.objects.filter(entry__in=[
        r.entry
        for r in shown_receipts])
    read_entries = [r.entry for r in read_entries]
    unread_entries = [r.entry
                      for r in shown_receipts
                      if r.entry not in read_entries
                      and r not in to_be_shown]

    user_featureset = []
    
    for e in read_entries:
        user_featureset.append(
            (extract_features(e), 'interesting'))
    for e in unread_entries:
        user_featureset.append(
            (extract_features(e), 'not_interesting'))

    return NaiveBayesClassifier.train(user_featureset)


def train_positivenb(user, feed=None):
    get_word_features(user)

    if (feed == None):
        shown_receipts = ReceivedEntry.objects.filter(
            reader_user=user,
            showed_to_user=True).order_by('-entry__pub_date')[:500]
    else:
        shown_receipts = ReceivedEntry.objects.filter(
            reader_user=user,
            entry__feed=feed,
            showed_to_user=True).order_by('-entry__pub_date')[:200]
    read_entries = ReadEntry.objects.filter(entry__in=[
        r.entry
        for r in shown_receipts])
    read_entries = [r.entry for r in read_entries]

    unread_entries = [r.entry for r in shown_receipts if r.entry not in read_entries]
    if not unread_entries:
        unread_entries = ReceivedEntry.objects.filter(
            reader_user=user).exclude(id__in=[r.id for r in read_entries]).order_by('-entry__pub_date')[:200]
        unread_entries = [r.entry for r in unread_entries]
    print len(read_entries), len(unread_entries), len(shown_receipts)
    read_sample = random.sample(read_entries, len(read_entries))
    unread_sample = random.sample(unread_entries, len(unread_entries)/2)
    read_featureset = [extract_features(e) for e in read_sample]
    unread_featureset = [extract_features(e) for e in unread_sample]

    return PositiveNaiveBayesClassifier.train(read_featureset, unread_featureset, float(len(read_entries))/len(shown_receipts))


def classify(entry, classifier):
    features = extract_features(entry)
    return classifier.classify(features)
