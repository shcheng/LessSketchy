#!/usr/bin/python 

#
# splits the sample into 4 sets 
# for crossvalidation
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
print "<> Clean-up process done!"

# creates 4 independent sample sets
n_legit = len(legit_clean)
n_scams = len(scams_clean)
legit_clean_arr = []
scams_clean_arr = []
for i in range(4):
    if i<3:
        legit_clean_arr.append(legit_clean[i*(n_legit/4):(i+1)*(n_legit/4)])
        scams_clean_arr.append(scams_clean[i*(n_scams/4):(i+1)*(n_scams/4)])
    else:
        legit_clean_arr.append(legit_clean[i*(n_legit/4):])
        scams_clean_arr.append(scams_clean[i*(n_scams/4):])

prf_arr    = []
fscore_arr = []
for i in range(4):
    print i, '...',
    legit_clean = legit_clean_arr[i]
    scams_clean = scams_clean_arr[i]
    # get the normalized price and coordinate matrix
    nprice, coordMat = reviewTool.get_nprice_and_coordMat(legit_clean)
    #print "<> Got normalized prices and coordinates"
    # Get the training metrics
    legit_metric = metric.Metric(legit_clean, coordMat, nprice)
    legit_farr   = legit_metric.format_metrics()
    scams_metric = metric.Metric(scams_clean, coordMat, nprice)
    scams_farr   = scams_metric.format_metrics()
    #print "<> Got the metrics"
    ### Data Training ###
    brf = bRandomForest.BalRandomForest(legit_farr, scams_farr)
    brf.allocate_test_sample()
    brf.train(1000)
    #brf.pickle_trained_model('../pickle_jar/ensembleModel_scan12_v1.pickle')
    # Get some validations
    conf_mat = brf.get_confusion_matrix(brf.test_sample[:, :-1],
                                        brf.test_sample[:, -1],
                                        0.5)
    prf = brf.get_precision_recall(conf_mat)
    fscore = (2.*(prf[0]*prf[1])/(prf[0]+prf[1]))
    prf_arr.append(prf)
    fscore_arr.append(fscore)
    print 'done'

