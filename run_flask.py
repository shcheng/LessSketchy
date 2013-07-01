from flask import Flask
from flask import request
from flask import render_template

import socket
import json
import query
import metric
import frontFormating as ff
import bRandomForest as brf
import pickle
import numpy as np

app = Flask(__name__)

# Load the ensemble models
clf_model  = pickle.load(open('./pickle_jar/ensembleModel_scan11_v1.pickle', 'r'))
print "<> Training model loaded"

# Load coordMat and npriceList info
coordMat   = pickle.load(open('./pickle_jar/coordMat_scan11_v1.pickle', 'r'))
npriceList = pickle.load(open('./pickle_jar/npriceList_scan11_v1.pickle', 'r'))
print "<> coord and normalized data loaded"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search-results')
def search_results():
    #search_terms = request.form['text']
    search_terms = request.args.get('text', None)
    search_terms = search_terms.lower()
    search_terms = search_terms.split()

    # Scrape and process listing
    q = query.Query(search_terms)
    post_listing  = q.scrape(5)
    # Get the feature array
    m = metric.Metric(post_listing, coordMat, npriceList)
    feature_arr = m.format_metrics()
    # Setup the classifier
    ensemble = brf.BalRandomForest()
    ensemble.load_model(clf_model)
    post_score = ensemble.predict(feature_arr) 

    post_links = []
    for p in range(len(post_listing)):
        modal_label = "ModalPost" + str(p)
        label, message = ff.get_sketchyLevel(post_score[p])
        hint_str = ff.get_hint(feature_arr[p])
        post_links.append((post_listing[p]['head'], 
                           post_listing[p]['link'],
                           label, 
                           message,
                           hint_str,
                           modal_label,
                           post_listing[p]['post']))

    return render_template('search-results.html', post_links=post_links)

@app.route('/examples')
def examples():
    # Setup classifier
    ensemble = brf.BalRandomForest()
    ensemble.load_model(clf_model)

    # legit test sample
    legit_fpath  = './test_sample/hist_cl_legit_20130625-1650.json'
    legit_json   = json.load(open(legit_fpath, 'r'))[:10]
    legit_metric = metric.Metric(legit_json, coordMat, npriceList)
    legit_farr   = legit_metric.format_metrics()
    legit_score  = ensemble.predict(legit_farr)
    legit_heads  = []
    for p in range(len(legit_json)):
        modal_label = 'ModalLegit' + str(p)
        label, message = ff.get_sketchyLevel(legit_score[p])
        hint_str = ff.get_hint(legit_farr[p])
        legit_heads.append((legit_json[p]['head'],
                            legit_json[p]['post'],
                            label,
                            message,
                            hint_str,
                            modal_label))
    
    # scams test sample
    scams_fpath  = './test_sample/hist_cl_scams_20130625-1650.json'
    scams_json   = json.load(open(scams_fpath, 'r'))[:10]
    scams_metric = metric.Metric(scams_json, coordMat, npriceList)
    scams_farr   = scams_metric.format_metrics()
    scams_score  = ensemble.predict(scams_farr)
    scams_heads  = []
    for p in range(len(scams_json)):
        modal_label = 'ModalScams' + str(p)
        label, message = ff.get_sketchyLevel(scams_score[p])
        hint_str = ff.get_hint(scams_farr[p])
        scams_heads.append((scams_json[p]['head'],
                            scams_json[p]['post'],
                            label,
                            message,
                            hint_str,
                            modal_label))


    return render_template('examples.html', 
                           legit_tSample=legit_heads, scams_tSample=scams_heads)

if __name__ == '__main__':
    if socket.gethostbyname(socket.gethostname()).startswith('172'):
        address = '0.0.0.0'
        portNum = 80
        app.debug = False
    else:
        address = '127.0.0.1'
        portNum = 5000
        app.debug = True
    app.run(address, port=portNum)
