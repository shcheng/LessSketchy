#!/usr/bin/python 

#
# This script is used to train the model with the scraped and 
# separated data (legit and scams). It generates a pickled
# ensemble model.
#

import os
import re
import json
import numpy as np
import bRandomForest
import reviewTool
import metric

#def main():
### Data Prep ###
list_files = os.listdir('./')
list_files.sort()
# This assumes that half of the files are legit and half 
# are the corresponding scams
mid_idx = len(list_files)/2
legit = reviewTool.patch_listings(list_files[:mid_idx])
scams = reviewTool.patch_listings(list_files[mid_idx:])
# remove duplicates
legit_clean = reviewTool.remove_duplicates([legit])
scams_clean = reviewTool.remove_duplicates([scams])
# remove noPosts
legit_clean = reviewTool.remove_noPosts(legit_clean)
scams_clean = reviewTool.remove_noPosts(scams_clean)
# reprocess phone numbers (just in case)
legit_clean = reviewTool.reprocess_phoneNumber_flag(legit_clean)
scams_clean = reviewTool.reprocess_phoneNumber_flag(scams_clean)
# get the normalized price and coordinate matrix
nprice, coordMat = reviewTool.get_nprice_and_coordMat(legit_clean)
# Get the training metrics
legit_metric = metric.Metric(legit_clean, coordMat, nprice)
legit_farr   = legit_metric.format_metrics()
scams_metric = metric.Metric(scams_clean, coordMat, nprice)
scams_farr   = scams_metric.format_metrics()
### Data Training ###
brf = bRandomForest.BalRandomForest(legit_farr, scams_farr)
brf.allocate_test_sample()
brf.train(1000)
brf.pickle_trained_model('../pickle_jar/ensembleModel_scan06_v4.pickle')
# Get some validations
conf_mat = brf.get_confusion_matrix(brf.test_sample[:, :-1],
                                    brf.test_sample[:, -1],
                                    0.5)
prf = brf.get_precision_recall(conf_mat)
fscore = (2.*(prf[0]*prf[1])/(prf[0]+prf[1]))
roc = brf.get_ROC_curve(brf.test_sample[:,:-1], brf.test_sample[:,-1], 
                        np.arange(0.01, 1, 0.01))

"""
### Model validation ###
fscore = []
rp_metrics = []
for n in range(100):
    print "validation", n
    brf = bRandomForest.BalRandomForest(legit_farr, scams_farr)
    brf.allocate_test_sample()
    brf.train(100)
    #pred = emodel.ensemble_predict(emodel.test_sample[:, :-1])
    #clsf = emodel.ensemble_classify(emodel.test_sample[:, :-1])
    #roc_curve = emodel.get_ROC_curve(emodel.test_sample[:, :-1], 
    #                                 emodel.test_sample[:, -1],
    #                                 np.arange(0.01, 1.00, 0.01))

    conf_mat = brf.get_confusion_matrix(brf.test_sample[:, :-1],
                                        brf.test_sample[:, -1],
                                        0.5)
    prf = brf.get_precision_recall(conf_mat)
    rp_metrics.append(prf)
    fscore.append(2.*(prf[0]*prf[1])/(prf[0]+prf[1]))
"""

#if __name__ == '__main__':
#    main()
