#
# metrics.py
#
# To produce the feature array from the scraped data
#

import urllib2
import re
import numpy as np
import pandas as pd
import scipy.spatial as sp
from bs4 import BeautifulSoup

class Metric:
    """
    Process and condensed the data into feature arrays.
    The Metric object is initiated with a list of dictionaries.
    """

    def __init__(self, listing, coordMat, npriceList):
        """
        Initialize the metric object

        Input:  listing (pd dataframe), coordMat and npriceList (arrays)
        """
        self.listing    = pd.DataFrame(listing)
        self.coordMat   = coordMat
        self.npriceList = npriceList

    def format_metrics(self):
        """
        Properly calculates and extracts the metric features

        Output: an Nx7 array
        """
        loc_flag = np.array([1 if lat!=-1 else 0 for lat in self.listing.lat])
        phn_flag = np.array([1 if phn!=-1 else 0 for phn in self.listing.phone])
        nbr_flag = np.array([1 if nbr!=-1 else 0 for nbr in self.listing.nbr])
        prc_flag = np.array([1 if prc!=-1 else 0 for prc in self.listing.price])
        n_capfrac = self._get_cap_fraction(self.listing)
        nprice_diff = []
        for i in range(len(self.listing)):
            if self.listing.price[i]!=-1 and self.listing.nbr[i]!=-1 and \
               self.listing.lat[i]!=-1   and self.listing.lon[i]!=-1: 
                nprice = (self.listing.price[i]/(1.*self.listing.nbr[i]))
                nprice_diff.append(self._get_perc_diff(
                                   [self.listing.lon[i], self.listing.lat[i]], 
                                   nprice))
            else:
                nprice_diff.append(0)
        nprice_diff = np.array(nprice_diff)
        # make the previous arrays vertical
        loc_flag = loc_flag.reshape(len(loc_flag), 1)
        phn_flag = phn_flag.reshape(len(phn_flag), 1)
        nbr_flag = nbr_flag.reshape(len(nbr_flag), 1)
        prc_flag = prc_flag.reshape(len(prc_flag), 1)
        n_capfrac = n_capfrac.reshape(len(n_capfrac), 1)
        nprice_diff = nprice_diff.reshape(len(nprice_diff), 1)
        n_words = self._get_n_words(self.listing).reshape(len(self.listing), 1)
        # concatenate them
        return np.concatenate((loc_flag, phn_flag, nbr_flag, prc_flag,
                               n_capfrac, n_words, nprice_diff), axis=1)

    ## Price related methods ##
    def _get_median_nprice(self, loc_arr):
        """
        Calculate the median price based on the nearest 20 apartments

        Input:  location array (1x2)
        Output: array of median normalized prices
        """
        # the first argument needs a 2d array
        dist_arr = sp.distance.cdist([loc_arr], self.coordMat)[0]  
        # use the 20 nearest neighbors
        top_dist_arr_idx = np.argsort(dist_arr)[1:21] 
        return np.median(self.npriceList[top_dist_arr_idx])

    def _get_perc_diff(self, loc_arr, nprice):
        """
        Returns the fractional difference w.r. to the location
        and normalized price

        Input:  location array, norm. price
        Output: fractional difference (Nx1)
        """
        return (nprice - self._get_median_nprice(loc_arr)) \
               / self._get_median_nprice(loc_arr)

    ## Text related methods ##
    def _get_cap_fraction(self, listing):
        """
        Calculates the fraction of capital letters

        Input:  listing in pd dataframe
        Output: array of cap fraction
        """
        ncapfrac = []  
        for post in listing.post:
            n_cap   = len(re.findall('[A-Z]', post))            
            n_total = len(post) * 1. 
            ncapfrac.append(n_cap/n_total)
        return np.array(ncapfrac)

    def _get_n_words(self, listing):
        """
        Returns the number of words in the main post text

        Input:  listing in pd dataframe
        Output: array of number of words
        """
        n_words = []
        for post in listing.post:
            n_words.append(len(post.split()))    
        return np.array(n_words)

