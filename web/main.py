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
from jinja2 import Template, Environment, BaseLoader, meta
from passlib.hash import md5_crypt



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

@app.route('/skillets', methods=['GET'])
def GetAllSnippets():
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

@app.route('/snippet', methods=['POST'])
def GetSnippet():
    data = request.json

    filters = data['filters']
    skillet = data['skillet']

    firestore = Firestore()
    docs = firestore.GetDocumentSnaps(skillet, filters)
    print("Query returned {} docs".format(len(docs)))
    l = []
    for doc_ref in docs:
        doc_dict = doc_ref.to_dict()
        if 'template_variables' in data:
            pt = template(doc_dict["path"], data['template_variables'])
            xt = template(doc_dict["xml"], data['template_variables'])
            if not pt:
                return error_message("Missing required template variables.")
            if not xt:
                return error_message("Missing required template variables.")
            doc_dict["path"] = pt
            doc_dict["xml"] = xt


        l.append(doc_dict)
    return flask.jsonify(l)


def error_message(msg):
    j = {
        "result": "error",
        "msg": msg
    }
    return flask.jsonify(j)

def template(str, context):
    e = Environment(loader=BaseLoader)
    e.filters["md5_ hash"] = md5_hash

    ast = e.parse(str)
    vars = meta.find_undeclared_variables(ast)
    for v in vars:
        if v not in context:
            print("Missing var: {}".format(v))
            return
    t = e.from_string(str)

    return(t.render(context))

# define functions for custom jinja filters
def md5_hash(txt):
    '''
    Returns the MD5 Hashed secret for use as a password hash in the PanOS configuration
    :param txt: text to be hashed
    :return: password hash of the string with salt and configuration information. Suitable to place in the phash field
    in the configurations
    '''
    return md5_crypt.hash(txt)