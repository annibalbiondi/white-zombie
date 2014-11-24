# coding=utf-8
import os
import codecs
import re
import locale
from nltk.classify import NaiveBayesClassifier
from nltk.tokenize import word_tokenize
from reader.models import ReaderUser, Entry, ReadEntry, ReceivedEntry, Feed

all_title_words = set()
all_description_words = set()

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def remove_stopwords(words):
    this_dir = os.path.dirname(__file__)
    stopwords = None

    with codecs.open(os.path.join(this_dir,
                                  'documents',
                                  'stopwords.txt'),
                     'r', encoding='utf-8') as stopwords_file:
        stopwords = word_tokenize(stopwords_file.read(stopwords_file))
    
    non_stopwords = set()
    for w in words:
        if w.lower() not in stopwords:
            non_stopwords.add(w.lower())

    return non_stopwords


def remove_html_tags(text):
    result = ' '.join(re.split(r'<.*>', text, 0, re.LOCALE |
                               re.UNICODE | re.DOTALL))
    return result


def slugify(text):
    new_text = remove_html_tags(text)

    return ' '.join(re.split(r'\s\d+|\W\s', new_text, 0,
                             re.LOCALE | re.UNICODE | re.DOTALL))

def get_word_features(user):
    shown_receipts = user.entries_received.filter(showed_to_user=True)
    
    for r in shown_receipts:
        all_title_words.update(remove_stopwords(
                word_tokenize(r.entry.title)))

        htmlless_description = remove_html_tags(r.entry.description)
        slug_description = slugify(htmlless_description)
        all_description_words.update(
            remove_stopwords(word_tokenize(slug_description)))


def extract_features(entry):
    features = dict()
    title_words = remove_stopwords(word_tokenize(entry.title))
    
    htmlless_description = remove_html_tags(entry.description)
    slug_description = slugify(htmlless_description)
    description_words = remove_stopwords(word_tokenize(slug_description))
    feed = entry.feed

    for word in all_title_words:
        features['title_contains(%s)' % word] = (word in title_words)
    for word in all_description_words:
        features['description_contains(%s)' % word] = (word in description_words)
    features['from_feed'] = feed
    return features


def train_classifier(user):
    get_word_features(user)
    shown_receipts = user.entries_received.filter(showed_to_user=True)
    # TODO tentar criar um QuerySet ao invés de uma lista
    user_entries_read = [r.entry for r in user.entries_read.all()]
    user_featureset = list()
    
    print 'entries read'
    for r in shown_receipts:
        if r.entry in user_entries_read:
            user_featureset.append((extract_features(r.entry), 'read'))
            print r.entry
        else:
            user_featureset.append((extract_features(r.entry), 'no_read'))

    return NaiveBayesClassifier.train(user_featureset)


def classify(entry, classifier):
    features = extract_features(entry)
    return classifier.classify(features)
