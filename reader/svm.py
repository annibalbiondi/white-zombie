from sklearn import svm

class SvmClassifier:

    def __init__(self, classifier, vocabulary):
        self._classifier = classifier
        self._vocabulary = vocabulary

    def classify(self, featureset):
        coordinates = []
        
        for word in self._vocabulary:
            coordinates.append(featureset.count(word))

        return self._classifier.predict([coordinates]) # TODO dar um jeito nesse array do numpy

    @staticmethod
    def build(user_featuresets):
        vocabulary = []
        label_vector = []
        feature_frequency = {}

        # construir vocabulario e contar o numero de vezes que as palavras presentes em cada instancia ocorrem
        #i = 0
        for featureset, label in user_featuresets:
            #index = str(i)
            for feature in featureset:
                if feature not in vocabulary:
                    vocabulary.append(feature)
                    #feature_frequency[feature] = {}
                #if not feature_frequency[feature].get(index):
                    #feature_frequency[feature][index] = 0
                #feature_frequency[feature][index] += 1
            label_vector.append(1 if label == 'interesting' else -1)
            #i += 1

        training_sample = []
        #i = 0

        for featureset, label in user_featuresets:
            coordinates = []
            #index = str(i)
            
            #for word in vocabulary:
                #if feature_frequency[word].get(index):
                    #coordinates.append(feature_frequency[word][index])
                #else:
                    #coordinates.append(0)
            for word in vocabulary:
                coordinates.append(featureset.count(word))
            training_sample.append(coordinates)
            #i += 1

        # usar training_sample e label_vector pra criar o svc do scikit
        classifier = svm.LinearSVC()
        classifier.fit(training_sample, label_vector)

        return SvmClassifier(classifier, vocabulary)
