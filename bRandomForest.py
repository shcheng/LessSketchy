#
# bRandomForest.py
#
# A implementation of balanced random forest based
# on an ensemble of CARTs from scikit-learn.
#

import pickle
import numpy as np
from sklearn.tree import DecisionTreeClassifier

class BalRandomForest:
    """
    Implementation of a balanced random forest based
    on an ensemble of CARTs
    """

    def __init__(self, legit, scams, train_size=0.8):
        """
        Initializes the BRF.

        Input:  legit feature array, scams feature array
                (no class tags!)
        """
        self.tagged_legit = legit
        self.tagged_scams = scams
        self.test_sample  = np.array([[]])
        self.train_sample = np.array([[]])
        self.estimators   = []
        self._add_tags()
        self._train_size = train_size

    def _add_tags(self):
        """
        Add class tags to the legit and scam feature arrays
        """
        n_legit = len(self.tagged_legit)
        n_scams = len(self.tagged_scams)
        legit_tags = np.zeros(n_legit).reshape(n_legit, 1) 
        scams_tags = np.ones(n_scams).reshape(n_scams, 1)
        self.tagged_legit = np.concatenate((self.tagged_legit, legit_tags), axis=1) 
        self.tagged_scams = np.concatenate((self.tagged_scams, scams_tags), axis=1)
        # randomize them
        self.tagged_legit = self.tagged_legit[np.random.permutation(len(self.tagged_legit))]
        self.tagged_scams = self.tagged_scams[np.random.permutation(len(self.tagged_scams))]

    def allocate_test_sample(self):
        """
        Allocates and stores the 
        testing sample for later use.
        """
        test_size = int((1.-self._train_size)*len(self.tagged_scams)) 
        self.test_sample = np.concatenate((self.tagged_legit[-test_size:, :],
                                           self.tagged_scams[-test_size:, :]),
                                           axis=0)
        rnd_idx = np.random.permutation(len(self.test_sample))
        self.test_sample = self.test_sample[rnd_idx, :] 

    def _prep_bal_data(self):
        """
        This is an bootstraped balanced training set. It can 
        be used for the resampling validation.
        """
        test_size = int((1.-self._train_size)*len(self.tagged_scams))
        train_scams_size = len(self.tagged_scams)-test_size
        train_legit_size = len(self.tagged_legit)-test_size
        rem_scams = self.tagged_scams[:train_scams_size]
        rem_legit = self.tagged_legit[:train_legit_size] 
        # booststrap
        boot_scams = rem_scams[np.random.permutation(len(rem_scams))]
        boot_legit = rem_legit[np.random.permutation(len(rem_legit))]
        rnd_idx = np.random.randint(train_scams_size, size=train_scams_size)
        boot_legit = boot_legit[rnd_idx, :]
        rnd_idx = np.random.randint(train_scams_size, size=train_scams_size)
        boot_scams = boot_scams[rnd_idx, :]   
        # join and randomize the sets
        train_sample = np.concatenate((boot_scams, boot_legit), axis=0)
        self.train_sample = train_sample[np.random.permutation(len(train_sample))]

    def train(self, n_estimators=1000): 
        """
        Trains the balanced random forest

        Input:  number of estimators (default 1000)
        """
        self.estimators = []
        for n in range(n_estimators):
            self._prep_bal_data()
            clf = DecisionTreeClassifier(max_features="auto")
            clf.fit(self.train_sample[:, :-1], self.train_sample[:, -1])
            self.estimators.append(clf)

    def predict(self, x):
        """
        Returns the prediction (betwen 0 and 1)

        Input:  feature array
        """
        prediction = []
        for clf in self.estimators:
            prediction.append(clf.predict(x))
        prediction = np.array(prediction)
        return np.mean(prediction, axis=0)

    def classify(self, x, threshold=0.5):
        """
        Returns the classification according to the threshold

        Input:  feature array, threshold (default 0.5)
        Output: classification (0 or 1)
        """
        pred = self.predict(x)
        scams_idx = (pred>=threshold)
        classification = np.zeros(len(pred))
        classification[scams_idx] = 1
        return classification

    def validate(self, x, x_tag):
        """
        Returns validation metrics:
            error rate
            false positive
            false negative

        Input:  feature array, class array
        """
        clsf = self.classify(x)
        err_idx = (clsf!=x_tag)
        err  = sum(err_idx)/(1.*len(err_idx))  
        n_fpos = 0
        n_fneg = 0
        for t in range(len(x_tag)):
            if x_tag[t] and not clsf[t]:
                n_fneg += 1
            elif not x_tag[t] and clsf[t]:
                n_fpos += 1
            else:
                continue
        fpos = n_fpos/(len(x_tag)*1.)
        fneg = n_fneg/(len(x_tag)*1.)
        return err, fpos, fneg

    def get_confusion_matrix(self, x, x_tag, threshold=0.5):
        """
        Returns the confusion matrix
        """
        clsf = self.classify(x, threshold)
        # Correct predictions
        true_idx = (clsf==x_tag)
        true_positive = sum(x_tag[true_idx])
        true_negative = sum((x_tag[true_idx]-1)*(-1))  # inverts the tags
        # Wrong predictions 
        false_idx = (clsf!=x_tag)
        false_positive = sum((x_tag[false_idx]-1)*(-1)) # inverts the tags
        false_negative = sum(x_tag[false_idx])
        return np.array([[true_negative, false_negative],   #   tn  fn
                         [false_positive, true_positive]])  #   fp  tp

    def get_precision_recall(self, conf_matrix):
        """
        Returns the precision and recall rate
        """
        tn = conf_matrix[0][0] 
        fn = conf_matrix[0][1]
        fp = conf_matrix[1][0]
        tp = conf_matrix[1][1]
        precision = tp / (tp + fp)  
        recall    = tp / (tp + fn)  # or true positive rate
        fpos_rate = fp / (tn + fp)  # or false alarm rate
        return precision, recall, fpos_rate

    def get_recall_precision_curve(self, x, x_tag, threshold_arr):
        """
        Returns the recall vs precision curve
        """
        curve = []
        for t in threshold_arr:
            conf_mat = self.get_confusion_matrix(x, x_tag, t)
            precision, recall, fpos_rate = self.get_precision_recall(conf_mat)
            curve.append([recall, precision])
        return np.array(curve)

    def get_ROC_curve(self, x, x_tag, threshold_arr):
        """
        Returns the ROC curve
        """
        roc = []
        for t in threshold_arr:
            roc.append(self.get_ROC_point(x, x_tag, t))
        roc = np.array(roc) 
        return roc

    def get_ROC_point(self, x, x_tag, threshold=0.5):
        """
        Calculate the ROC point for a given threshold
        """
        conf_mat = self.get_confusion_matrix(x, x_tag, threshold)
        precision, recall, fpos_rate = self.get_precision_recall(conf_mat)
        return np.array([fpos_rate, recall])

    def pickle_trained_model(self, fname):
        """
        Pickles the trained model
        """
        pickle.dump(self.estimators, open(fname, 'w'))
