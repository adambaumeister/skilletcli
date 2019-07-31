from google.cloud import firestore
import os

GCLOUD_API_VAR="GOOGLE_APPLICATION_CREDENTIALS"
GCLOUD_PROJECT="skillet-deploy"

class Firestore():
    """
    Methods for interacting with gcloud-firestore for the storage and retrieval of PAN skillets.
    """
    def __init__(self, debug=False):
        self.default_cred_loc = os.getcwd() + os.sep + ".gcp-credentials.json"
        self.debug = debug
        # make sure we have valid gcloud creds
        creds = self.check_creds()
        if not creds:
            raise ValueError("Missing required API credentials file".format(GCLOUD_API_VAR))

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

    def add_snippets(self, snippets, collection_name, stack_name, skillet_type):
        print("Adding {} snippets to Firestore/{}.".format(len(snippets), collection_name))
        b = self.db.batch()
        for snippet in snippets:
            d = {
                "name": snippet.name,
                "path": snippet.xpath,
                "xml": snippet.xmlstr,
                "type": skillet_type,
                "stack": stack_name,
            }
            self.log(d)
            doc_ref = self.db.collection(collection_name).document(snippet.name)
            b.set(doc_ref, d)
        
        b.commit()