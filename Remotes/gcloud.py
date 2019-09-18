import requests
from .skillet import *

class Gcloud():
    """
    Remote skillet retrieval from Gcloud based API

    This class is for client-side utilties.
    """
    def __init__(self, url):
        self.url = url

    def Query(self, skillet_name, type, stack, snippet_names, major_version, context):
        """
        Query the skillet API.
        :param skillet_name: Name of skillet, such as iron-skillet, to query
        :param type: Device type (panorama|panos)
        :param stack: Stack to retrieve snippets from (snippets)
        :param snippet_names: List of snippets to retrieve
        :param context: Template variables
        :param panos_version:
        :return: List of Snippet instances.
        """
        QUERY = {
            "skillet": skillet_name,
            "filters": {
                "name": snippet_names,
                "type": type,
                "stack": stack,
                "panos_version": major_version,
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

    def List(self, skillet_name, **kwargs):
        params = []
        for k,v in kwargs.items():
            params.append('{}={}'.format(k,v))

        qs = "&".join(params)

        if len(params) > 0:
            res = requests.get(self.url + "/snippet?skillet={}&{}".format(skillet_name, qs))
        else:
            res = requests.get(self.url + "/snippet?skillet={}&{}".format(skillet_name, qs))

        j = res.json()
        return j