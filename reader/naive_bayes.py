# coding=utf-8
import math

class NaiveBayesClassifier:

    def __init__(self, labels, prior_prob, feature_condprob):
        self._labels = labels
        self._prior_prob = prior_prob
        self._feature_condprob = feature_condprob

    def classify(self, featureset):
        score = {}

        for label in self._labels:
            score[label] = math.log(self._prior_prob[label])
            for feature in featureset:
                if self._feature_condprob.get(feature):
                    score[label] += math.log(
                        self._feature_condprob[feature][label])

        return max(score.iteritems(), key=lambda s: s[1])[0]

    @staticmethod
    def train(labeled_featuresets):
        labels = set()
        vocabulary = set()
        number_of_instances = {}
        feature_frequency = {}
        smoothing = 1

        for featureset, label in labeled_featuresets:
            if label not in labels:
                labels.add(label)
                number_of_instances[label] = 1
            else:
                number_of_instances[label] += 1

            for feature in featureset:
                if feature not in vocabulary:
                    vocabulary.add(feature)
                    feature_frequency[feature] = {}
                if not feature_frequency[feature].get(label):
                    feature_frequency[feature][label] = 1
                else:
                    feature_frequency[feature][label] += 1

        prior_prob = {}
        feature_condprob = {}

        for label in labels:
            prior_prob[label] = (float(number_of_instances[label])/
                                 len(labeled_featuresets))
            feature_instances = 0

            for feature in vocabulary:
                if not feature_frequency[feature].get(label):
                    feature_frequency[feature][label] = 0
                feature_instances += feature_frequency[feature][label]
                if not feature_condprob.get(feature):
                    feature_condprob[feature] = {}

            for feature in vocabulary:
                feature_condprob[feature][label] = (
                    float(feature_frequency[feature][label] + smoothing)/
                    (feature_instances + smoothing*len(vocabulary)))

        return NaiveBayesClassifier(labels, prior_prob, feature_condprob)
