#
# reviewTool.py
#
# This is a collection of functions to facilitate 
# the reviewing of posts and to determine whether they
# are legit or scams.
#

import os 
import json
import urllib2
import bs4
import re
import numpy as np
import pandas as pd

def separate_posts(path):
    """
    This function encapsulates the entire post reviewing
    processes: scraping (2nd run), duplicate removal,
    and the actual reviewing to split posts between 
    legit and scams.

    Input:  path to the json files of 1st run scrapes
    Output: legit and scams list of dictionaries
    """
    listing_json = get_scrapped_list(path)
    listing_df = remove_duplicates(listing_json)
    legit, scams = review_listing(listing_df)
    legit = reprocess_phoneNumber_flag(legit)
    scams = reprocess_phoneNumber_flag(scams)
    return legit, scams

def remove_duplicates(list_of_json):
    """
    Remove the duplicates and returns
    a pandas dataframe with unique entries.

    Input:  list of dictionaries
    Output: pandas data frame
    """
    listing_df = pd.DataFrame()
    for json_entry in list_of_json:
        json_buffer = pd.DataFrame(json_entry)
        listing_df = pd.concat((listing_df, json_buffer))
    listing_df.index = range(len(listing_df))
    listing_df = listing_df.drop_duplicates(cols='pid')
    listing_df.index = range(len(listing_df))
    return listing_df

def remove_noPosts(listing_pd):
    """
    Takes a pandas listing dataframe and returns a cleaned up 
    listing without the noPosts posts
    """
    idx_wPost = listing_pd['hasPost']==1
    listing_pd = listing_pd[idx_wPost]
    listing_pd.index = range(len(listing_pd))
    return listing_pd

def patch_listings(json_fname_list):
    """
    Patches up a list of json dictionaries
    """
    patched_list = []
    for fname in json_fname_list:
        curr_listing = json.load(open(fname, 'r'))
        for post in curr_listing:
            patched_list.append(post)
    return patched_list

def get_scrapped_list(path):
    """
    Gets the sorted (latest files first) list of 
    json file names to be patched
    """
    list_of_files = os.listdir(path)
    list_of_json = []
    for fname in list_of_files: 
        list_of_json.append(json.load(open(fname, 'r')))
    return list_of_json

def get_listing_dict(list_df):
    """
    Converts the dataframe into a dictionary (json-like)
    """
    return list_df.T.to_dict()

def clean_post_text(text):
    """
    Clean up text of unwanted remnant tags and other 
    html stuff
    """
    clean_text = re.sub('<.*>', '', repr(listing_text[0]))
    clean_text = re.sub('\n|\t', ' ', listing_text_clean)
    return clean_text

def review_listing(list_df):
    """
    Review each of the listing to check whether it has
    been removed or not.

    Input:  a pandas dataframe of the listing 
    Output: legit and scams list of dictionaries
    """
    n = 0
    listing_dict = get_listing_dict(list_df)
    listing_scams = []
    listing_legit = []
    listing_links = np.array(list_df['link'])
    for idx in range(len(listing_links)):
        print "%d / %d" %(n, len(listing_links)), listing_links[idx]
        n += 1
        try:
            page = urllib2.urlopen(listing_links[idx])
        except:
            print "  ----> Bad link (skip it!)"
            continue
        post_soup = bs4.BeautifulSoup(page)
        post_text = post_soup.find_all('section', attrs={'id':'postingbody'})
        post_dict = {} 
        if len(post_soup.find_all('div', attrs={'class':'removed'}))>0:
            removal_clause = str(
                post_soup.find_all('div', attrs={'class':'removed'})[0]
            )
            match = re.search('flagged for removal', removal_clause)
            if match:
                listing_scams.append(listing_dict[idx])
            else:
                listing_legit.append(listing_dict[idx])
        else:
            listing_legit.append(listing_dict[idx])
    return listing_legit, listing_scams 

def reprocess_phoneNumber_flag(list_df):
    """
    This method corrects the bug in misidentifying phone 
    numbers using re.match.

    Input:  panda dataframe
    Output: panda dataframe
    """
    for i in range(len(list_df)):
        phone_match = re.findall('\d{3}\W*\d{3}\W*\d{4}', list_df.post[i])
        phone = 0
        if len(phone_match)>0:
            phone = int(re.sub(r'\W', '', phone_match[0]))
        else:
            phone = -1
        list_df.phone[i] = phone
    return list_df

def get_nprice_and_coordMat(legit_df):
    """
    Returns the legit listing normalized price array
    coordinate matrix (2d array).
    
    Input:  legit listing dataframe
    Output: array of normalized prices and array of pair coordinates
    """
    #legit_listing = pd.DataFrame(legit_listing)
    wInfo_idx = (legit_df.price!=-1) * \
                (legit_df.lon!=-1)   * \
                (legit_df.lat!=-1)   * \
                (legit_df.nbr!=-1)
    coord_lon = np.array(legit_df.lon[wInfo_idx])
    coord_lat = np.array(legit_df.lat[wInfo_idx])
    coordMat = np.concatenate((coord_lon.reshape(len(coord_lon), 1), 
                               coord_lat.reshape(len(coord_lat), 1)),
                               axis=1)
    npriceList = np.array(legit_df.price[wInfo_idx] \
               / legit_df.nbr[wInfo_idx])
    return npriceList, coordMat
