import os
import sys
import oyaml
import requests
from xml.etree import ElementTree
from jinja2 import Template
from urllib3.exceptions import ProtocolError
from jinja2.exceptions import TemplateAssertionError
from colorama import init as colorama_init
import re
from colorama import Fore, Back, Style
import getpass
import argparse
from Remotes import Git

"""
Create-and-push
Generates PANOS configuration from the XML snippets and adds to the PANOS device.

This way you can pick and choose the aspects of iron-skillet you want without removing your entire configuration.

Usage:
    python create_and_push.py
    With no arguments, lists all available snippets and their destination xpaths
    
    python create_and_push.py snippetname1 snippetname2 
    Push the listed snippetnames
"""
# Index of git based skillet repositories
GIT_SKILLET_INDEX = {
    "iron-skillet": "https://github.com/PaloAltoNetworks/iron-skillet.git"
}
class Panos:
    """
    PANOS Device. Could be a firewall or PANORAMA.
    """
    def __init__(self, addr, user, pw):
        """
        Initialize a new panos object
        :param addr: NAME:PORT combination (ex. l72.16.0.1:443)
        :param user: username
        :param pw: password
        """
        self.url = "https://{}/api".format(addr)
        self.user = user
        self.pw = pw
        self.key = ''
        self.debug = False
        self.connect()


    def connect(self):
        """
        Connect to a PANOS device and retrieve an API key.
        :return: API Key
        """
        params = {
            "type": "keygen",
            "user": self.user,
            "password": self.pw,
        }
        r = self.send(params)
        if not check_resp(r, print_result=False):
            print("Error on login received from PANOS: {}".format(r.text))
            exit(1)

        root = ElementTree.fromstring(r.content)
        elem = root.findall("./result/key")
        self.key = elem[0].text
        return self.key

    def send(self, params):
        """
        Send a request to this PANOS device
        :param params: dict: GET parameters for query ({ "type": "op" })
        :return: GET Response type
        """
        url = self.url
        params["key"] = self.key
        self.debug_log("{} : {}".format(url, params))
        try:
            r = requests.get(url, params=params, verify=False)
        except ProtocolError:
            print("Failed to send a rqequest.")
            exit(1)
        return r

    def get_type(self):
        """
        Get the type of PANOS device using show system info
        :param panos: PANOS device object
        :return:
        """
        params = {
            "type": "op",
            "cmd": "<show><system><info></info></system></show>"
        }
        r = self.send(params)
        root = ElementTree.fromstring(r.content)
        elem = root.findall("./result/system/model")
        return elem[0].text

    def debug_log(self, l):
        if self.debug:
            print(l)

def create_context(config_var_file):
    # read the metafile to get variables and values
    try:
        with open(config_var_file, 'r') as var_metadata:
            variables = oyaml.safe_load(var_metadata.read())

    except IOError as ioe:
        fail_message = """
        Could not open the variables file.
        
        A variables file containing variable defintions is required to template the XML snippets.
        
        See the README.md file for more information.
        
        """
        print(f'Could not open metadata file {config_var_file}')
        print(ioe)
        print(fail_message)
        sys.exit()

    # grab the metadata values and convert to key-based dictionary
    jinja_context = dict()

    for snippet_var in variables['variables']:
        jinja_context[snippet_var['name']] = snippet_var['value']

    return jinja_context

def sanitize_element(element):
    """
    Eliminate some undeeded characters out of the XML snippet if they appear.
    :param element: element str
    :return: sanitized element str
    """
    element = re.sub("\n\s+", "", element)
    element = re.sub("\n", "", element)
    return element

def set_at_path(panos, xpath, elementvalue):
    """
    Runs a "set" action against a given xpath.
    :param panos: .panos object
    :param xpath: xpath to set at
    :param elementvalue: Element value to set
    :return: GET Response page
    """
    params = {
        "type": "config",
        "action": "set",
        "xpath": xpath,
        "element": sanitize_element(elementvalue),
    }
    r = panos.send(params)
    return r


def get_type(panos):
    """
    Get the type of PANOS device using show system info
    :param panos: PANOS device object
    :return:
    """
    params = {
        "type": "op",
        "cmd": "<show><system><info></info></system></show>"
    }
    r = panos.send(params)
    root = ElementTree.fromstring(r.content)
    elem = root.findall("./result/system/model")
    return elem[0].text

def env_or_prompt(prompt, prompt_long=None, secret=False):
    k = "SKCLI_{}".format(prompt).upper()
    e = os.getenv(k)
    if e:
        return e

    if secret:
        e = getpass.getpass(prompt + ": ")
        return e

    if prompt_long:
        e = input(prompt_long)
        return e

    e = input(prompt + ": ")
    return e

def check_resp(r, print_result=True):
    root = ElementTree.fromstring(r.content)
    status = root.attrib["status"]
    if status == "success":
        if print_result:
            print("{}Success!{}".format(Fore.GREEN, Style.RESET_ALL))
        return True
    else:
        if print_result:
            print("{}{} : Failed.{}".format(Fore.RED, r.text, Style.RESET_ALL))
        return False



def main():
    parser = argparse.ArgumentParser(description="Deploy a Skillet to a PANOS device from one of the possible repo types.")
    parser.add_argument('--repository', default="iron-skillet", metavar="repo_name", help="Name of skillet to use ({})"
                        .format(", ".join(GIT_SKILLET_INDEX.keys())))
    parser.add_argument('--repotype', default="git", help="Type of skillet repo")
    parser.add_argument("--config", default="config_variables.yaml", help="Path to YAML variable configuration file.")
    parser.add_argument("--snippetstack", default="snippets", help="Snippet stack to use. ")
    parser.add_argument("--branch", help="Git repo branch to use.")
    parser.add_argument("--refresh", help="Refresh the cloned repository directory.", action='store_true')
    parser.add_argument("snippetnames", help="List of snippets to push by name.", nargs="*")
    args = parser.parse_args()

    if args.repotype == "git":
        repo_url = GIT_SKILLET_INDEX[args.repository]
        repo_name = args.repository
        g = Git(repo_url)
        g.clone(repo_name, ow=args.refresh)
        if args.branch:
            g.branch(args.branch)

        sc = g.build()
    else:
        print("No other skillet types currently supported.")
        exit(1)

    requests.packages.urllib3.disable_warnings()
    colorama_init()
    if len(args.snippetnames) == 0:
        print("printing available {} snippets".format(repo_name))
        sc.print_all_skillets()
        sys.exit(0)
    else:
        addr = env_or_prompt("address", prompt_long="address:port (localhost:9443) of PANOS Device to configure: ")
        user = env_or_prompt("username")
        pw = env_or_prompt("password", secret=True)
        fw = Panos(addr, user, pw)
        t = fw.get_type()

        # This is unneeded i think.
        if t != "Panorama":
            t = "panos"

        skillet = sc.get_skillet(t)
        context = create_context(args.config)
        skillet.template(context)
        for snippet in skillet.select_snippets(args.snippetstack, args.snippetnames):
            print("Doing {} at {}...".format(snippet.name, snippet.rendered_xpath), end="")
            r = set_at_path(fw, snippet.rendered_xpath, snippet.rendered_xmlstr)
            check_resp(r)


if __name__ == '__main__':
    main()
