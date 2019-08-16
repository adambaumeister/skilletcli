import requests
from .skillet import *

class Gcloud():
    """
    Remote skillet retrieval from Gcloud based API

    This class is for client-side utilties.
    """
    def __init__(self, url):
        self.url = url

    def Query(self, skillet_name, type, stack, snippet_names, context):
        """
        Query the skillet API.
        :param skillet_name: Name of skillet, such as iron-skillet, to query
        :param type: Device type (panorama|panos)
        :param stack: Stack to retrieve snippets from (snippets)
        :param snippet_names: List of snippets to retrieve
        :param context: Template variables
        :return: List of Snippet instances.
        """
        QUERY = {
            "skillet": skillet_name,
            "filters": {
                "name": snippet_names,
                "type": type,
                "stack": stack,
            },
            "template_variables": context
        }
        res = requests.post(self.url + "/snippet", json=QUERY).json()
        snippets = []
        for sjson in res:
            snippet = Snippet(
                sjson['path'],
                sjson['xml']
            )
            # Because the snippet API does it for us, setup the rendered strings automatically
            snippet.rendered_xmlstr = snippet.xmlstr
            snippet.rendered_xpath = snippet.xpath
            snippets.append(snippet)

        return snippets

    def List(self, skillet_name, t, stack_name):
        res = requests.get(self.url + "/snippet?skillet={}&stack={}&type={}".format(skillet_name, stack_name, t))
        j = res.json()
        return j