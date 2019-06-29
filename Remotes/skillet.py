from jinja2 import Template, Environment, BaseLoader
from passlib.hash import des_crypt
from passlib.hash import md5_crypt
from passlib.hash import sha512_crypt
from xml.etree import ElementTree

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
        self.snippet_stack = {}
        self.type = skillet_type
        self.supported_versions = supported_versions

    def new_snippet(self, name, xmlstr):
        s = Snippet(name, xmlstr)
        return s

    def add_snippets(self, snippets):
        self.snippet_stack = snippets

    def get_snippets(self):
        return self.snippet_stack

    def print_all_snippets(self):
        for name, snippets in self.snippet_stack.items():
            print("  " + name)
            for snippet in snippets:
                print("    " + snippet.name)

    def template(self, context):
        for name, snippets in self.snippet_stack.items():
            for snippet in snippets:
                snippet.template(context)

    def select_snippets(self, stack_name, names):
        r = []
        for snippet in self.snippet_stack[stack_name]:
            if snippet.name in names:
                # If it needs to be split up
                r = r + self.split_snippet(snippet)

        return r

    def split_snippet(self, snippet):
        """
        Cuts an oversized snippet into smaller snippets on the basis that most snippets are
        a list of <entry> objects
        :param snippet_string:
        :return:
        """
        snippet_string = snippet.rendered_xmlstr
        length = len(snippet_string)

        if length > 12000:
            # Wrap the xml in root elements so we can parse it
            snippet_string = "<root>" + snippet_string + "</root>"
            root = ElementTree.fromstring(snippet_string)
            elems = root.findall("./entry")
        else:
            return [snippet]

        new_snippets = []
        if not elems:
            print("Error: Oversized snippet that cannot be split, exiting.")
            exit(1)

        for e in elems:
            xmlstr = ElementTree.tostring(e)
            xmlstr = xmlstr.decode("utf-8")
            s = snippet.copy()
            s.rendered_xmlstr = xmlstr
            new_snippets.append(s)

        return new_snippets

class Snippet:
    """
    Snippet represents an XML blob along with some metadata such as xpath and required variables
    """
    def __init__(self, xpath, xmlstr):
        self.xpath = xpath
        self.xmlstr = xmlstr
        self.metadata = {}
        self.name = ""

        self.rendered_xpath = ""
        self.rendered_xmlstr = ""

    def get_xpath(self):
        return self.xpath

    def set_metadata(self, metadata):
        self.metadata = metadata
        
    def template(self, context):
        e = Environment(loader=BaseLoader)
        e.filters["md5_hash"] = md5_hash

        t = e.from_string(self.xpath)
        self.rendered_xpath = t.render(context)

        t = e.from_string(self.xmlstr)
        self.rendered_xmlstr = t.render(context)

    def copy(self):
        s = Snippet(self.xpath, self.xmlstr)
        s.rendered_xmlstr = self.rendered_xmlstr
        s.rendered_xpath = self.rendered_xpath
        return s

# define functions for custom jinja filters
def md5_hash(txt):
    '''
    Returns the MD5 Hashed secret for use as a password hash in the PanOS configuration
    :param txt: text to be hashed
    :return: password hash of the string with salt and configuration information. Suitable to place in the phash field
    in the configurations
    '''
    return md5_crypt.hash(txt)