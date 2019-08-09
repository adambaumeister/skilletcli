"""
API (programmatic) access to Firestore hosted skillet collections.

Quickstart Dev
App creds aren't required when deployed, just for development.
```
    set GOOGLE_APPLICATION_CREDENTIALS=.gcp-credentials.json
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
import re
# This hack lets us check the current directory for packages
# while not breaking the way appengine sees it
sys.path.append('.')
sys.path.append('web')
import flask
from flask import request, redirect
from db import Firestore
from jinja2 import Template, Environment, BaseLoader, meta
from passlib.hash import md5_crypt
from webfuncs import ValidRequest


app = flask.Flask(__name__)

VALID_FILTERS = [
    "type",
    "stack",
    "path",
]
@app.route('/', methods=['GET'])
def GetCollections():
    firestore = Firestore()
    collections = firestore.GetCollections()
    return flask.jsonify(collections)

@app.route('/apidocs', methods=['GET'])
def DocsRedirect():
    return redirect("/docs/index.html", 302)


def list_snippets(skillet_name):
    firestore = Firestore()
    filters = {}
    for k, v in request.args.items():
        if k in VALID_FILTERS:
            filters[k] = v

    docs = firestore.GetDocumentSnaps(skillet_name, filters)
    print("Query returned {} docs".format(len(docs)))
    l = []
    for doc_ref in docs:
        l.append(doc_ref.to_dict())
    return l

@app.route('/snippet', methods=['GET', 'POST'])
def GetSnippet():
    firestore = Firestore()

    # If GET request, list all the snippets instead.
    if request.method == 'GET':
        vr = ValidRequest(required_args=['skillet'])
        if not vr.parse(request):
            return error_message("Missing skillet value."), 405

        skillet_name = vr.get('skillet')

        snippets = list_snippets(skillet_name)
        result = []
        for s in snippets:
            result.append(s['name'])

        return flask.jsonify(result)

    # Otherwise, get the specific snippet
    data = request.json

    filters = data['filters']
    skillet = data['skillet']
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

@app.route('/search', methods=['GET'])
def SearchSnippets():
    ra = ['skillet', 'search']
    search_fields = ['name', 'path']
    vr = ValidRequest(required_args=ra)
    if not vr.parse(request):
        return error_message("Missing required args {}.".format(ra)), 405

    skillet_name = vr.get('skillet')
    search_string = vr.get('search')
    snippets = list_snippets(skillet_name)
    r = []
    for s in snippets:
        match = False
        for sf in search_fields:
            if re.search(search_string, s[sf]):
                match = True
        if match:
            r.append(s)

    return flask.jsonify(r)


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