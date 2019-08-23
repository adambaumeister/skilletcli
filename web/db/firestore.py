from google.cloud import firestore
import os

GCLOUD_API_VAR="GOOGLE_APPLICATION_CREDENTIALS"
GCLOUD_PROJECT="skillet-deploy"
META_COLLECTION="db"
META_DOCUMENT="meta"
META_SCHEMA={
    "collections": []
}
class Firestore():
    """
    Methods for interacting with gcloud-firestore for the storage and retrieval of PAN skillets.

    This class is for server-side utilities - it requires valid gcloud service account credentials.
    """
    def __init__(self, debug=False):
        self.default_cred_loc = os.getcwd() + os.sep + ".gcp-credentials.json"
        self.debug = debug

        self.db = self.connect()

    def connect(self):
        db = firestore.Client(GCLOUD_PROJECT)
        return db

    def check_creds(self):
        r = os.getenv(GCLOUD_API_VAR)
        if r:
            self.log("Found creds via environment variable {}".format(os.getenv(GCLOUD_API_VAR)))
            return os.getenv(GCLOUD_API_VAR)

        if os.path.exists(self.default_cred_loc):
            self.log("Found creds via default location {}".format(self.default_cred_loc))
            os.environ[GCLOUD_API_VAR] = self.default_cred_loc
            return self.default_cred_loc

        return False

    def log(self, msg):
        if self.debug:
            print(msg)

    def GetCollections(self):
        """
        Retrieve all of the currently uploaded Skillets (Collections)
        :return: ([]string): List of collections.
        """
        meta = self.get_meta()
        return meta.Get_Collections()

    def AddSkilletCollection(self, sc):
        """
        Takes a SkilletCollection object and uploads all skillets to Firestore.
        :param sc: SkilletCollection object
        :return: Records added
        """
        # Panorama|panos
        for skillet_type in sc.get_skillet_names():
            sk = sc.get_skillet(skillet_type)
            # 'snippets'
            for stack in sk.get_all_stacks():
                # Select the actual snippets, give all
                snippets = sk.select_snippets(stack, ["all"])
                self.add_snippets(snippets, sc.name, stack, skillet_type)

    def GetDocumentRefs(self, collection_name, filters={}):
        ref = self.db.collection(collection_name)
        docs = ref.stream()
        r = []
        for d in docs:
            doc_dict = d.to_dict()
            print(doc_dict)
            if self.dict_comparison(doc_dict, filters):
                r.append(d.reference)
        return r

    def GetDocumentSnaps(self, collection_name, filters={}):
        ref = self.db.collection(collection_name)
        docs = ref.stream()
        r = []
        for d in docs:
            doc_dict = d.to_dict()
            if self.dict_comparison(doc_dict, filters):
                r.append(d)
        return r

    def dict_comparison(self, d, filters):
        match = True
        for k, v in filters.items():
            if k in d:
                if type(v) == list:
                    if d[k] not in v:
                        match = False
                elif v != d[k]:
                    match = False

            else:
                match = False

        return match

    def get_meta(self):
        """
        Retrieve the metadata of the skillet-deploy firestore
        :return: Data
        """
        doc_ref = self.db.collection(META_COLLECTION).document(META_DOCUMENT)
        meta = Meta(doc_ref)
        return meta

    def rebuild(self):
        m = self.get_meta()
        m.delete()

    def add_snippets(self, snippets, collection_name, stack_name, skillet_type):
        """
        Adds n snippets to the provided Firestore collection (skillet name) with the given field values
        :param snippets: Snippet class instances
        :param collection_name: Name of firestore collection to add to
        :param stack_name: Snippet stack association (eg. snippets)
        :param skillet_type: Type of device skillet targets (panos|panorama)
        :return: (int): total number of changes to firestore db
        """
        print("Adding {} snippets to Firestore/{}.".format(len(snippets), collection_name))
        # Add the skillet as a collection to the Firestore DB
        # This requires updating the DB "meta" schema document.
        meta = self.get_meta()
        meta.Add_Collection(collection_name)

        b = self.db.batch()
        filters ={
            "stack": stack_name,
            "type": skillet_type,
        }
        # Delete all the matching records first.
        doc_refs = self.GetDocumentRefs(collection_name, filters)
        print("Deleting {} existing docs.".format(len(doc_refs)))
        for ref in doc_refs:
            b.delete(ref)
        b.commit()
        total_changes = len(doc_refs) + len(snippets)
        b = self.db.batch()
        for snippet in snippets:
            d = {
                "name": snippet.name,
                "path": snippet.xpath,
                "xml": snippet.xmlstr,
                "type": skillet_type,
                "stack": stack_name,
                "skillet": collection_name
            }
            self.log(d)
            doc_ref = self.db.collection(collection_name).document()
            b.set(doc_ref, d)

        b.commit()
        return total_changes

class Meta:
    """
    Meta class
    Handles operations related to the "meta" document, which contains schema information for the firestore db.
    """
    def __init__(self, ref):
        meta_doc = ref.get().to_dict()

        if not meta_doc:
            meta_doc = META_SCHEMA
        self.doc = meta_doc

        self.ref = ref

    def Add_Collection(self, collection):
        if collection in self.doc['collections']:
            return
        self.doc['collections'].append(collection)
        self.ref.set(self.doc)

    def Get_Collections(self):
        return self.doc['collections']

    def delete(self):
        self.ref.delete()