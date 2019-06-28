
class SkilletCollection:
    """
    Skillet collection Class

    Store of skillets. A skillet is a combination of XML snippets and metadata
    associated with a pan device type and software verison.
    """
    def __init__(self):
        self.skillet_map = {}
        return

    def new_skillet(self, skillet_name, skillet_type, supported_versions):
        s = Skillet(skillet_name, skillet_type, supported_versions)
        self.skillet_map[skillet_name] = s
        return s

class Skillet:
    def __init__(self, name, skillet_type, supported_versions):
        self.name = name
        self.snippets = {}
        self.type = skillet_type
        self.supported_versions = supported_versions

    def new_snippet(self, name, xmlstr):
        s = Snippet(name, xmlstr)
        return s

    def add_snippets(self, snippets):
        self.snippets = snippets

class Snippet:
    """
    Snippet represents an XML blob along with some metadata such as xpath and required variables
    """
    def __init__(self, xpath, xmlstr):
        self.xpath = xpath
        self.xmlstr = xmlstr