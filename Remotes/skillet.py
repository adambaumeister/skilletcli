from jinja2 import Template

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

    def get_skillet(self, skillet_name):
        return self.skillet_map[skillet_name]

    def print_all_skillets(self):
        for name, skillet in self.skillet_map.items():
            print(name)
            skillet.print_all_snippets()


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

    def get_snippets(self):
        return self.snippets

    def print_all_snippets(self):
        for name, snippets in self.snippets.items():
            print("  " + name)
            for snippet in snippets:
                print("    " + snippet.xpath)

class Snippet:
    """
    Snippet represents an XML blob along with some metadata such as xpath and required variables
    """
    def __init__(self, xpath, xmlstr):
        self.xpath = xpath
        self.xmlstr = xmlstr
        self.metadata = {}

        self.rendered_xpath = ""
        self.rendered_xmlstr = ""

    def get_xpath(self):
        return self.xpath

    def set_metadata(self, metadata):
        self.metadata = metadata
        
    def template(self, context):
        t = Template(self.xpath)
        self.rendered_xpath = t.render(context)

        t = Template(self.xpath)
        self.rendered_xmlstr = t.render(context)