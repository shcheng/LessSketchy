#
# scrapeTool.py
#
# The main scrape tool class for web-scraping
# and data formating for storing
#

import urllib2
import re
import json
import time
from bs4 import BeautifulSoup

class ScrapeTool:
    """
    A client to deal with the data scraping from Craigslist.
    The scraping process usually consist on two run. In the 
    first run or stage (this class' role), the posts are web-scraped 
    without prejudice. In the second run, the previously scraped 
    posts are reviewed to check for scams.
    """

    def __init__(self, n=1000):
        """
        Initialize with the number of posts to be scraped.
        The input is rounded to the nearest 100th. 
        The default is 1000. 
        """
        n = n - (n%100)
        self.url_root = "http://sfbay.craigslist.org"
        self.posting_lvl_list = ['']
        for i in range(100, n+1, 100): 
            lvl_string = 'index' + '%s' % str(i) + '.html'
            self.posting_lvl_list.append(lvl_string)
        self._listing_pristine = []

    def scrape(self):
        """
        Start scraping Craig's list!
        """
        for posting_lvl in self.posting_lvl_list:
            url = self.url_root + '/apa/' + posting_lvl
            print url
            page = urllib2.urlopen(url)
            soup = BeautifulSoup(page)
            curr_listing = soup.find_all('p', attrs={'class':'row'})
            for listing in curr_listing:
                # listing_info : [pid, head, lon, lat, prc, nbr]
                listing_info = self._extract_listing_info(listing)
                # listing_link
                listing_link = self.url_root + str(listing.a['href'])
                page = urllib2.urlopen(listing_link)
                listing_soup = BeautifulSoup(page)
                # Check for 'removed tag'
                if len(listing_soup.find_all('div', attrs={'class':'removed'}))==0:
                    listing_text = listing_soup.find_all('section', attrs={'id':'postingbody'})
                    listing_text_clean = self._clean_text(listing_text)
                    # extract phone number
                    phone = self._extract_phone_number(listing_text_clean)
                    listing_dict = self._store_listing(listing_info, listing_link, 
                                                      phone, listing_text_clean)
                    self._listing_pristine.append(listing_dict)
                else:
                    continue
        print "Done scraping"

    def dump_scraped_listing(self):
        """
        Dumps the list of dictionaries into a json file.
        """
        time_stamp = self._get_time_stamp()
        out_pristine_fname = 'hist_cl_posts' + time_stamp + '.json'
        json.dump(self._listing_pristine, open(out_pristine_fname, 'w'))

    def _get_time_stamp(self):
        """
        Get nicely formatted time stamp
        """
        yr = str(time.localtime().tm_year)
        mo = self._add_zeros(time.localtime().tm_mon)
        dy = self._add_zeros(time.localtime().tm_mday)
        hr = self._add_zeros(time.localtime().tm_hour)
        mn = self._add_zeros(time.localtime().tm_min)
        return '_' + yr + mo + dy + '-' + hr + mn

    def _add_zeros(self, value):
        """
        If value is one digit add preceding 0.
        The input value is an int, but the return
        value is string
        """
        value_str = str(value)
        if value<10: 
            value_str = '0' + value_str
        return value_str

    def _extract_listing_info(self, listing):
        """
        Extracts info from the listing input (beautiful soup tag)
        and returns a list of the following parameters:
                pid, head, lon, lat, prc, nbr
        (in this order).
        """
        nbr_match = re.search(' / [0-9]br - ', str(listing))
        prc_match = re.search('\$\d+', str(listing))
        head = listing.find_all('a')[1].string
        pid = int(listing.get('data-pid'))
        # Check for presence of location
        if listing.has_attr('data-longitude') and \
           listing.has_attr('data-latitude'):
            lon = float(listing.get('data-longitude'))
            lat = float(listing.get('data-latitude'))
        else:
            lon = -1
            lat = -1
        # Check for presence of # of rooms
        if nbr_match!=None:
            nbr = int(re.sub('[ /a-z-]*', '', nbr_match.group()))
        else:
            nbr = -1
        # Check for presence of price
        if prc_match!=None:
            #price_str = listing.find('span', attrs={'class':'price'}).string
            #price = float(re.sub('\$', '', price_str))
            price_str = prc_match.group()
            price = float(re.sub('\$', '', str(prc_match.group())))
        else:
            price = -1
        return [pid, head, lon, lat, price, nbr]

    def _clean_text(self, listing_text):
        """
        Given a list of body text (possibly one element list) this
        method return the cleaned up body text or an empty string 
        if no text is found.
        """
        if len(listing_text)>0:
            listing_text_clean = ' '.join(listing_text[0].findAll(text=True))
            listing_text_clean = re.sub('\n|\t', ' ', listing_text_clean)
            listing_text_clean = re.sub('\s+', ' ', listing_text_clean)
            listing_text_clean = re.sub("'", '', listing_text_clean)
            listing_text_clean = re.sub('"', '', listing_text_clean)
        else:
            listing_text_clean = ' ' 
        return listing_text_clean 

    def _extract_phone_number(self, listing_text_clean):
        """
        Extracts the phone number from the post body text.
        The input argument is a list (possibly) with just one element
        or an empty array (if no text if found in the post body).
        It returns a
        """
        if len(listing_text_clean.split())>0:
            phone_match = re.findall('\d{3}\W*\d{3}\W*\d{4}', listing_text_clean)
            if len(phone_match)>0:
                phone = int(re.sub(r'\W', '', phone_match[0]))
            else:
                phone = -1
        else:
            listing_text_clean = ' ' 
            phone = -1
        return phone

    def _store_listing(self, listing_info, listing_link, 
                       phone, listing_text_clean):
        """
        Returns the extracted listing info into a dictionary
        """
        listing_dict = {}
        listing_dict['pid']   = listing_info[0] 
        listing_dict['head']  = listing_info[1]
        listing_dict['lon']   = listing_info[2]
        listing_dict['lat']   = listing_info[3]
        listing_dict['price'] = listing_info[4]
        listing_dict['nbr']   = listing_info[5]
        listing_dict['phone'] = phone
        listing_dict['link']  = listing_link
        if len(listing_text_clean.split())>0:
            listing_dict['post'] = listing_text_clean
            listing_dict['hasPost'] = 1
        else:
            listing_dict['post'] = ''
            listing_dict['hasPost'] = 0
        return listing_dict
