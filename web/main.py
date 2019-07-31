"""
API (programmatic) access to Firestore hosted skillet collections.

Quickstart Dev
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
import flask
from db import Firestore

app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def GetCollections():
    firestore = Firestore()
    collections = firestore.GetCollections()
    return flask.jsonify(collections)
