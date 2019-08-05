import requests
class Gcloud():
    """
    Remote skillet retrieval from Gcloud based API

    This class is for client-side utilties.
    """
    def __init__(self, url):
        self.url = url

    def Query(self, skillet_name, stack, snippet_names, filters=None):
        QUERY = {
            "skillet": skillet_name,
            "filters": filters,
            "template_variables": {
                "SINKHOLE_IPV4": "1.1.1.1",
                "SINKHOLE_IPV6": "::1",
            }
        }