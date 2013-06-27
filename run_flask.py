from flask import Flask
from flask import request
from flask import render_template

import socket
import query
import metric
import frontFormating as ff
import bRandomForest as brf
import pickle
import numpy as np

app = Flask(__name__)

# Load the ensemble models
clf_model  = pickle.load(open('./pickle_jar/ensembleModel_scan11_v1.pickle', 'rb'))
print "<> Training model loaded"

# Load coordMat and npriceList info
coordMat   = pickle.load(open('./pickle_jar/coordMat_scan11_v1.pickle', 'rb'))
npriceList = pickle.load(open('./pickle_jar/npriceList_scan11_v1.pickle', 'rb'))
print "<> coord and normalized data loaded"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def search_results():
    search_terms = request.form['text']
    search_terms = search_terms.lower()
    search_terms = search_terms.split()

    # Scrape and process listing
    q = query.Query(search_terms)
    post_listing  = q.scrape(10)
    # Get the feature array
    m = metric.Metric(post_listing, coordMat, npriceList)
    feature_arr = m.format_metrics()
    # Setup the classifier
    ensemble = brf.BalRandomForest()
    ensemble.load_model(clf_model)
    post_score = ensemble.predict(feature_arr) 

    post_links = []
    for p in range(len(post_listing)):
        label, message = ff.get_sketchyLevel(post_score[p])
        hint_str = ff.get_hint(feature_arr[p])
        post_links.append((post_listing[p]['head'], 
                           post_listing[p]['link'],
                           label, 
                           message,#))
                           hint_str))

    return render_template('search-results.html', post_links=post_links)

if __name__ == '__main__':
    if socket.gethostbyname(socket.gethostname()).startswith('54'):
        address = '0.0.0.0'
        portNum = 80
        app.debug = False
    else:
        address = '127.0.0.1'
        portNum = 5000
        app.debug = True
    app.run(address, port=portNum)
