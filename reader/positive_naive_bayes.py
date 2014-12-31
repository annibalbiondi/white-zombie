# coding=utf-8
from reader.naive_bayes import NaiveBayesClassifier

class PositiveNaiveBayesClassifier(NaiveBayesClassifier):

    @staticmethod
    def train(positive_featuresets, unlabeled_featuresets, positive_prior_prob):
        labels = set(1, -1)
        vocabulary = set()
        prior_prob = {'1': positive_prior_prob,
                      '-1': 1 - positive_prior_prob}
        feature_condprob = {}
        feature_frequency = {}
        smoothing = 1

        for featureset in positive_featuresets:
            for feature in featureset:
                if feature not in vocabulary:
                    vocabulary.add(feature)
                    feature_condprob[feature] = {}
                if not feature_condprob[feature].get('1'):
                    feature_condprob[feature]['1'] = 1
                else:
                    feature_condprob[feature]['1'] += 1

        for featureset in unlabeled_featuresets:
            for feature in featureset:
                if feature not in vocabulary:
                    vocabulary.add(feature)
                    feature_frequency[feature] = 0
                feature_frequency[feature] += 1

        features_instances = 0

        for feature in vocabulary:
            if not feature_condprob[feature].get('1'):
                feature_condprob[feature]['1'] = 0
                feature_condprob[feature]['1'] += smoothing
                feature_condprob[feature]['1'] = float(feature_condprob[feature]['1'])/(feature_frequency[feature] + smoothing*len(vocabulary))
            features_instances += feature_frequency[feature]

        for feature in vocabulary:
            feature_condprob[feature]['-1'] = ((float(feature_frequency[feature])/feaures_instances) - feature_condprob['1']*prior_prob['1'])/prior_prob['-1']
            if feature_condprob[feature]['-1'] < 0:
                raise ValueError('probabilidade condicional negativa para atributo "' + feature + '" dado o rótulo -1')

        return PositiveNaiveBayesClassifier(labels, vocabulary, prior_prob, feature_condprob)
