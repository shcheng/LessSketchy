#
#   query.py
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
    """
    Query object to scrape and return a dictionary of posts
    """
    
    def __init__(self, query_terms):
        self.query_terms = query_terms 
        self.url_root = 'http://sfbay.craigslist.org'
        self.url = 'http://sfbay.craigslist.org/search/apa?zoomToPosting=&query=' 

    def scrape(self, n_post=10):
        """
        Scrape away!
        Scrapes n_post posts and returns all the relevant information
        as a list of dictionaries

        Input:  number of posts to scrape (real-time)
        Output: list of dictionaries
        """
        post_collection = []
        for q in self.query_terms:
            self.url = self.url + q + '+'
        self.url = self.url[:-1]
        page = urllib2.urlopen(self.url)
        soup = BeautifulSoup(page)
        listing = soup.find_all('p', attrs={'class':'row'})
        if len(listing)==0:
            return None
        for post in listing[:n_post]:
            nbr_match = re.search(' / [0-9]br - ', str(post))
            prc_match = re.search('\$\d+', str(post))
            head = post.find_all('a')[1].string
            pid = int(post.get('data-pid'))
            lon, lat = self._check_loc(post)      # Check for presence of location
            nbr = self._check_nbr(nbr_match)      # Check for presence of # of rooms
            price = self._check_prc(prc_match)    # Check for presence of price
            ### Posting main text body ###
            post_link = self.url_root + str(post.a['href'])
            page = urllib2.urlopen(post_link)
            post_soup = BeautifulSoup(page)
            # Check for 'removed tag'
            if len(post_soup.find_all('div', attrs={'class':'removed'}))==0:
                post_text = post_soup.find_all('section', attrs={'id':'postingbody'})
                if len(post_text)>0:
                    post_text_clean = self._clean_text(post_text[0])
                    phone_match = re.findall(r'\d{3}\W*\d{3}\W*\d{4}', post_text_clean)
                    if len(phone_match)>0:
                        phone = int(re.sub(r'\W', '', phone_match[0]))
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
            else:
                continue
        return post_collection

    def _clean_text(self, text):
        """
        Removes all unwanted and unnecessary symbols
        """
        post_text_clean = ' '.join(text.findAll(text=True))
        #post_text_clean = re.sub('<.*>', '', repr(text))
        post_text_clean = re.sub('\n|\t', ' ', post_text_clean)
        post_text_clean = re.sub(' +', ' ', post_text_clean)
        post_text_clean = re.sub("'", '', post_text_clean)
        post_text_clean = re.sub('"', '', post_text_clean)
        return post_text_clean

    def _check_loc(self, post):
        """
        Check for location presence
        """
        if post.has_attr('data-longitude') and \
           post.has_attr('data-latitude'):
            lon = float(post.get('data-longitude'))
            lat = float(post.get('data-latitude'))
        else:
            lon = -1
            lat = -1
        return lon, lat

    def _check_nbr(self, nbr_match):
        """
        Check for nbr info presence
        """
        if nbr_match!=None:
            nbr = int(re.sub('[ /a-z-]*', '', nbr_match.group()))
        else:
            nbr = -1
        return nbr

    def _check_prc(self, prc_match):
        """
        Check for price info presence
        """
        if prc_match!=None:
            price_str = prc_match.group()
            price = float(re.sub('\$', '', str(prc_match.group())))
        else:
            price = -1
        return price
