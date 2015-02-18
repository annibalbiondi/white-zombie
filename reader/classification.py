# coding=utf-8
import codecs
import locale
import os
import re
from reader.naive_bayes import NaiveBayesClassifier
from reader.positive_naive_bayes import PositiveNaiveBayesClassifier
#from reader.svm import SvmClassifier
from nltk.tokenize import RegexpTokenizer
from reader.models import ReaderUser, Entry, ReadEntry, ShownEntry, Feed

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

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
    result = ' '.join(re.split(r'<.*?>', text, 0,
                               re.UNICODE | re.DOTALL))
    return result


def slugify(text):
    new_text = remove_html_tags(text)

    return ' '.join(re.split(r'\s\d+|\W\s', new_text,
                             0, re.UNICODE))

def get_word_features(user):
    received_entries = ShownEntry.objects.filter(reader_user=user)
    all_title_words = []
    all_description_words = []
    for r in received_entries:
        all_title_words.extend(
            remove_stopwords(tokenizer.tokenize(r.entry.title)))
        
        slug_description = slugify(r.entry.description)
        all_description_words.extend(
            remove_stopwords(tokenizer.tokenize(slug_description)))


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

    shown_entries = ShownEntry.objects.filter(
        reader_user=user)
    read_entries = ReadEntry.objects.filter(
        reader_user=user)
    read_entries = [r.entry for r in read_entries]
    unread_entries = [r.entry
                      for r in shown_entries
                      if r.entry not in read_entries
                      and r.entry not in to_be_shown]
    user_featureset = []
    
    for e in read_entries:
        user_featureset.append(
            (extract_features(e), 'interesting'))
    for e in unread_entries:
        user_featureset.append(
            (extract_features(e), 'not_interesting'))

    return NaiveBayesClassifier.train(user_featureset)

"""
def train_positivenb(user, to_be_shown, feed=None):
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

    labeled_featureset = []
    
    for e in read_entries:
        labeled_featureset.append(extract_features(e))

    unlabeled_featureset = []

    for e in unread_entries:
        unlabeled_featureset.append(extract_features(e))

    return PositiveNaiveBayesClassifier.train(
        user_featureset, unlabeled_featureset,
        float(len(labeled_featureset))/
        (len(labeled_featureset) + len(unlabeled_featureset)))
"""

'''
def train_svm(user, to_be_shown, feed=None):
    get_word_features(user)

    #if (feed == None):
    shown_receipts = ReceivedEntry.objects.filter(
        reader_user=user,
        showed_to_user=True)
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

    return SvmClassifier.build(user_featureset)
'''

def classify(entry, classifier):
    features = extract_features(entry)
    return classifier.classify(features)
