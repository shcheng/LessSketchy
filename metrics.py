#
#   Collection of tools to facilitate extraction and 
#   processing of craigslist data
#
import urllib2
import re
import numpy as np
import pandas as pd
import scipy.spatial as sp
from bs4 import BeautifulSoup
from sklearn.ensemble import RandomForestClassifier as rfc

class Query:
    """Query object to scrape and return a dictionary of posts
    """
    
    def __init__(self, query_terms):
        self.query_terms = query_terms 
        self.url_root = 'http://sfbay.craigslist.org'
        self.url = 'http://sfbay.craigslist.org/search/apa?zoomToPosting=&query=' 

    def scrape(self, n_post=10):
        """Scrape away!
        Scrapes n_post posts and returns all the relevant information
        as a list of dictionaries
        """
        post_collection = []
        for q in self.query_terms:
            self.url = self.url + q + '+'
        self.url = self.url[:-1]
        page = urllib2.urlopen(self.url)
        soup = BeautifulSoup(page)
        listing = soup.find_all('p', attrs={'class':'row'})
        for post in listing[:n_post]:
            nbr_match = re.search(' / [0-9]br - ', str(post))
            prc_match = re.search('\$\d+', str(post))
            head = post.find_all('a')[1].string
            pid = int(post.get('data-pid'))
            lon, lat = self.check_loc(post)      # Check for presence of location
            nbr = self.check_nbr(nbr_match)      # Check for presence of # of rooms
            price = self.check_prc(prc_match)    # Check for presence of price
            ### Posting main text body ###
            post_link = self.url_root + str(post.a['href'])
            page = urllib2.urlopen(post_link)
            post_soup = BeautifulSoup(page)
            # Check for 'removed tag'
            if len(post_soup.find_all('div', attrs={'class':'removed'}))==0:
                post_text = post_soup.find_all('section', attrs={'id':'postingbody'})
                if len(post_text)>0:
                    post_text_clean = self.clean_text(post_text[0])
                    phone_match = re.findall(r'\d{3}\W*\d{3}\W*\d{4}', post_text_clean)
                    if len(phone_match)>0:
                        phone = int(re.sub(r'[\s\(\)-./\|]', '', phone_match[0]))
                    else:
                        phone = -1
                else:
                    post_text_clean = ' ' 
                    phone = -1
                post_dict = {}
                post_dict['pid'] = pid
                post_dict['head'] = head
                post_dict['lon'] = lon
                post_dict['lat'] = lat
                post_dict['nbr'] = nbr
                post_dict['price'] = price
                post_dict['phone'] = phone
                post_dict['link'] = post_link
                if len(post_text_clean.split())>0:
                    post_dict['post'] = post_text_clean
                    post_dict['hasPost'] = 1
                    post_collection.append(post_dict)
                else:
                    continue
                    #post_dict['post'] = ''
                    #post_dict['hasPost'] = 0
                #post_collection.append(post_dict)
            else:
                continue
        return post_collection

    def clean_text(self, text):
        """Removes all unwanted and 
        unnecessary symbols
        """
        post_text_clean = ' '.join(text.findAll(text=True))
        #post_text_clean = re.sub('<.*>', '', repr(text))
        post_text_clean = re.sub('\n|\t', ' ', post_text_clean)
        post_text_clean = re.sub(' +', ' ', post_text_clean)
        post_text_clean = re.sub("'", '', post_text_clean)
        post_text_clean = re.sub('"', '', post_text_clean)
        return post_text_clean

    def check_loc(self, post):
        """Check for location presence
        """
        if post.has_attr('data-longitude') and \
           post.has_attr('data-latitude'):
            lon = float(post.get('data-longitude'))
            lat = float(post.get('data-latitude'))
        else:
            lon = -1
            lat = -1
        return lon, lat

    def check_nbr(self, nbr_match):
        """Check for nbr info presence
        """
        if nbr_match!=None:
            nbr = int(re.sub('[ /a-z-]*', '', nbr_match.group()))
        else:
            nbr = -1
        return nbr

    def check_prc(self, prc_match):
        """Check for price info presence
        """
        if prc_match!=None:
            price_str = prc_match.group()
            price = float(re.sub('\$', '', str(prc_match.group())))
        else:
            price = -1
        return price


class Metric:
    """Process and condensed the data into feature arrays.
    The Metric object is initiated with a list of dictionaries.
    """

    def __init__(self, listing, coordMat, npriceList):
        self.listing    = pd.DataFrame(listing)
        self.coordMat   = coordMat
        self.npriceList = npriceList

    def format_metrics(self):
        loc_flag = np.array([1 if lat!=-1 else 0 for lat in self.listing.lat])
        phn_flag = np.array([1 if phn!=-1 else 0 for phn in self.listing.phone])
        nbr_flag = np.array([1 if nbr!=-1 else 0 for nbr in self.listing.nbr])
        prc_flag = np.array([1 if prc!=-1 else 0 for prc in self.listing.price])
        n_capfrac = self.get_cap_fraction(self.listing)
        nprice_diff = []
        for i in range(len(self.listing)):
            if self.listing.price[i]!=-1 and self.listing.nbr[i]!=-1 and \
               self.listing.lat[i]!=-1   and self.listing.lon[i]!=-1: 
                nprice = (self.listing.price[i]/(1.*self.listing.nbr[i]))
                #nprice_diff.append(self.get_nprice_bin(
                #                   [self.listing.lon[i], self.listing.lat[i]], 
                #                   nprice))
                nprice_diff.append(self.get_perc_diff(
                                   [self.listing.lon[i], self.listing.lat[i]], 
                                   nprice))
            else:
                #nprice_diff.append(1)
                nprice_diff.append(0)
        nprice_diff = np.array(nprice_diff)
        # make the previous arrays vertical
        loc_flag = loc_flag.reshape(len(loc_flag), 1)
        phn_flag = phn_flag.reshape(len(phn_flag), 1)
        nbr_flag = nbr_flag.reshape(len(nbr_flag), 1)
        prc_flag = prc_flag.reshape(len(prc_flag), 1)
        n_capfrac = n_capfrac.reshape(len(n_capfrac), 1)
        nprice_diff = nprice_diff.reshape(len(nprice_diff), 1)
        n_words = self.get_n_words(self.listing).reshape(len(self.listing), 1)
        # concatenate them
        return np.concatenate((loc_flag, phn_flag, nbr_flag, prc_flag,
                               n_capfrac, n_words, nprice_diff), axis=1)
     
    """
    def format_metrics(self):
        feature_arr = [] 
        for post in self.listing:
            tmp = np.zeros(5)
            tmp[0]=1 if post['lat']!=(-1) and post['lon']!=(-1) else 0
            tmp[1]=1 if post['phone']!=(-1) else 0
            tmp[2]=1 if post['nbr']!=(-1)   else 0
            tmp[3]=1 if post['price']!=(-1)   else 0
            if tmp[0] and tmp[2] and tmp[3]:
                nprice  = post['price']/(post['nbr']*1.)
                loc_arr = np.array([post['lon'], post['lat']])
                tmp[4] = self.get_nprice_bin(loc_arr, nprice)
            else:
                tmp[4] = 1
            feature_arr.append(tmp)
        return np.array(feature_arr)
    """

    ## Price related methods ##
    def get_median_nprice(self, loc_arr):
        # the first argument needs a 2d array
        dist_arr = sp.distance.cdist([loc_arr], self.coordMat)[0]  
        # use the 20 nearest neighbors
        top_dist_arr_idx = np.argsort(dist_arr)[1:21] 
        return np.median(self.npriceList[top_dist_arr_idx])

    def get_perc_diff(self, loc_arr, nprice):
        return (nprice - self.get_median_nprice(loc_arr)) \
               / self.get_median_nprice(loc_arr)

    def get_nprice_bin(self, loc_arr, nprice): 
        nprice_bin = 1
        if self.get_perc_diff(loc_arr, nprice)<(-0.34):
            nprice_bin = 0 
        elif self.get_perc_diff(loc_arr, nprice)>0.34:
            nprice_bin = 2
        else:
            nprice_bin = 1
        return nprice_bin

    ## Text related methods ##
    def get_cap_fraction(self, listing):
        ncapfrac = []   # legit section
        for post in listing.post:
            n_cap   = len(re.findall('[A-Z]', post))            
            n_total = len(post) * 1. 
            ncapfrac.append(n_cap/n_total)
        return np.array(ncapfrac)

    def get_n_words(self, listing):
        n_words = []
        for post in listing.post:
            n_words.append(len(post.split()))    
        return np.array(n_words)


class Ensemble:
    """Ensemble Random Forest (super-overkill) to be trained and used with 
    the metric arrays.
    """

    def __init__(self, clf_model):
        self.estimators = clf_model

    def epredict(self, x):
        prediction = []
        for clf in self.estimators:
            prediction.append(clf.predict(x))
        prediction = np.array(prediction)
        return np.mean(prediction, axis=0)

    def eclassify(self, x, threshold=0.5):
        pred = self.epredict(x)
        scams_idx = (pred>=threshold)
        classification = np.zeros(len(pred))
        classification[scams_idx] = 1
        return classification
