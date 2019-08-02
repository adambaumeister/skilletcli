"""
API (programmatic) access to Firestore hosted skillet collections.

Quickstart Dev
App creds aren't required when deployed, just for development.
```
    set GOOGLE_APPLICATION_CREDENTIALS=..\.gcp-credentials.json
    set FLASK_APP=main.py
    flask run
```

Quickstart Deployment
```
gcloud auth login
gcloud config set project skillet-deploy
gcloud app deploy
```
"""
import sys
# This hack lets us check the current directory for packages
# while not breaking the way appengine sees it
sys.path.append('.')
sys.path.append('web')
import flask
from flask import request
from db import Firestore

app = flask.Flask(__name__)

VALID_FILTERS = [
    "type",
    "stack",
]
@app.route('/', methods=['GET'])
def GetCollections():
    firestore = Firestore()
    collections = firestore.GetCollections()
    return flask.jsonify(collections)

@app.route('/skillet', methods=['GET'])
def GetSnippets():
    firestore = Firestore()
    filters = {}
    for k, v in request.args.items():
        if k in VALID_FILTERS:
            filters[k] = v

    docs = firestore.GetDocumentSnaps(request.args.get('skillet'), filters)
    print("Query returned {} docs".format(len(docs)))
    l = []
    for doc_ref in docs:
        l.append(doc_ref.to_dict())
    return flask.jsonify(l)