# coding=utf-8
import math

class NaiveBayesClassifier:

    def __init__(self, labels, vocabulary, prior_prob, feature_condprob):
        self._labels = labels
        self._vocabulary = vocabulary
        self._prior_prob = prior_prob
        self._feature_condprob = feature_condprob

    def vocabulary(self):
        return self._vocabulary

    def labels(self):
        return self._labels

    def prior_prob(self):
        return self._prior_prob

    def feature_condprob(self):
        return self._feature_condprob

    def classify(self, featureset):
        score = {}

        for label in self._labels:
            score[label] = math.log(self._prior_prob[label])
            for feature in featureset:
                if self._feature_condprob.get(feature):
                    score[label] += math.log(self._feature_condprob[feature][label])

        return max(score.iteritems(), key=lambda s: s[1])[0]

    @staticmethod
    def train(labeled_featuresets):
        labels = set()
        vocabulary = set()
        prior_prob = {}
        feature_condprob = {}
        feature_frequency = {}
        smoothing = 1

        for featureset, label in labeled_featuresets:
            if label not in labels:
                labels.add(label)
                prior_prob[label] = 1
            else:
                prior_prob[label] += 1

            for feature in featureset:
                if feature not in vocabulary:
                    vocabulary.add(feature)
                    feature_condprob[feature] = {}
                    feature_frequency[feature] = 0
                if not feature_condprob[feature].get(label):
                    feature_condprob[feature][label] = 1
                else:
                    feature_condprob[feature][label] += 1
                feature_frequency[feature] += 1

        for label in labels:
            prior_prob[label] = float(prior_prob[label])/len(labeled_featuresets)
            for feature in vocabulary:
                if not feature_condprob[feature].get(label):
                    feature_condprob[feature][label] = 0
                feature_condprob[feature][label] += smoothing
                feature_condprob[feature][label] = float(feature_condprob[feature][label])/(feature_frequency[feature] + smoothing*len(vocabulary))

        return NaiveBayesClassifier(labels, vocabulary, prior_prob, feature_condprob)
