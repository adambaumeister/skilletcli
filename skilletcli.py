import os
import sys
import oyaml
import requests
from yaml.scanner import ScannerError
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError
from urllib3.exceptions import ProtocolError
from colorama import init as colorama_init
import re
from colorama import Fore, Back, Style
import getpass
import argparse
from Remotes import Git, Gcloud
import json

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
    def __init__(self, addr, user, pw, connect=True, debug=False):
        """
        Initialize a new panos object
        :param addr: NAME:PORT combination (ex. l72.16.0.1:443)
        :param user: username
        :param pw: password
        :param connect (true): Specify whether to connect at init or not.
        """
        self.type_switch = {
            r'panorama': "panorama",
            r'm-': "panorama",
        }

        self.url = "https://{}/api".format(addr)
        self.user = user
        self.pw = pw
        self.key = ''
        if debug == True:
            self.log_level = 1
        else:
            self.log_level = 0

        self.log("Logging level is {}".format(self.log_level))
        if connect:
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
        self.log("Connecting to {}".format(self.url))
        r = self.send(params)
        if not self.check_resp(r):
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
        self.log("{} : {}".format(url, params), level=2)
        try:
            # = requests.get(url, params=params, verify=False)
            r = requests.post(url, data=params, verify=False)
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
        self.log("Sending: {}".format(params))

        r = self.send(params)
        if not self.check_resp(r):
            print("Error on login received from PANOS: {}".format(r.text))
            exit(1)

        root = ElementTree.fromstring(r.content)
        elem = root.findall("./result/system/model")
        t = elem[0].text
        type_result = self.get_type_from_info(t)
        self.log("Show sys model:{} Inferred type: {}".format(t, type_result))
        return type_result

    def get_type_from_info(self, t):
        for regex, result in self.type_switch.items():
            if re.search(regex, t.lower()):
                return result

        return "panos"

    def log(self, l, level=1):
        if level <= self.log_level:
            print(l)

    def check_resp(self, r):
        try:
            root = ElementTree.fromstring(r.content)
        except ParseError as e:
            print(r.content)
            print("{}".format(e))
            exit(1)

        status = root.attrib["status"]
        if status == "success":
            return True
        else:
            return False

def create_context(config_var_file):
    # read the metafile to get variables and values
    try:
        open(config_var_file, 'r')
    except IOError as ioe:
        fail_message = """{}Note: {} not found. Default variables for snippet stack will be used.{}
        """.format(Fore.YELLOW, config_var_file, Style.RESET_ALL)
        print(fail_message)
        return None

    try_json = False
    with open(config_var_file, 'r') as f:
        try:
            variables = oyaml.safe_load(f.read())
        except ScannerError:
            try_json = True

    if try_json:
        with open(config_var_file, 'r') as f:
            try:
                variables = json.load(f)
            except json.decoder.JSONDecodeError:
                print("Configuration file could not be decoded as YAML or JSON!")
                exit(1)

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
    element = re.sub(r"\n\s+", "", element)
    element = re.sub(r"\n", "", element)
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
    try:
        root = ElementTree.fromstring(r.content)
    except ParseError as e:
        print(r.content)
        print("{}".format(e))
        exit(1)

    status = root.attrib["status"]
    if status == "success":
        if print_result:
            print("{}Success!{}".format(Fore.GREEN, Style.RESET_ALL))
        return True
    else:
        if print_result:
            print("{}{} : Failed.{}".format(Fore.RED, r.text, Style.RESET_ALL))
        return False

def push_from_gcloud(args):
    """
    Pull snippets from Gcloud instead of Git repos.
    :param args: parsed args from argparse
    """
    colorama_init()
    addr = env_or_prompt("address", prompt_long="address or address:port of PANOS Device to configure: ")
    user = env_or_prompt("username")
    pw = env_or_prompt("password", secret=True)
    fw = Panos(addr, user, pw, debug=args.debug)
    t = fw.get_type()
    gc = Gcloud(args.repopath)
    context = create_context(args.config)
    snippets = gc.Query(args.repository, t, args.snippetstack, args.snippetnames, context)

    if len(args.snippetnames) == 0:
        print("printing available {} snippets".format(args.repository))
        sc.print_all_skillets(elements=args.print_entries)
        sys.exit(0)

    if len(snippets) == 0:
        print("{}Snippets {} not found for device type {}.{}".format(Fore.RED, ",".join(args.snippetnames), t,
                                                                     Style.RESET_ALL))
    for snippet in snippets:
        print("Doing {} at {}...".format(snippet.name, snippet.rendered_xpath), end="")
        r = set_at_path(fw, snippet.rendered_xpath, snippet.rendered_xmlstr)
        check_resp(r)

def push_skillets(args):
    """
    Based on user configuration (cmdline args), pushes given snippets to a PANOS device.
    :param args: parsed args from argparse
    """
    colorama_init()
    if args.repotype == "git":
        if args.repository not in GIT_SKILLET_INDEX:
            if not args.repopath:
                print("Non-registered skillet. --repopath [git url] is required.")
                exit(1)

            repo_url = args.repopath
        else:
            repo_url = GIT_SKILLET_INDEX[args.repository]

        repo_name = args.repository
        g = Git(repo_url)
        g.clone(repo_name, ow=args.refresh, update=args.update)
        if args.branch:
            if args.branch == "list":
                print("\n".join(g.list_branches()))
                exit()
            g.branch(args.branch)

        sc = g.build()
    elif args.repotype == "local":
        repo_name = args.repopath
        g = Git("")
        sc = g.build_from_local(args.repopath)
    else:
        print("No other skillet types currently supported.")
        exit(1)

    requests.packages.urllib3.disable_warnings()

    if len(args.snippetnames) == 0:
        print("printing available {} snippets".format(repo_name))
        sc.print_all_skillets(elements=args.print_entries)
        sys.exit(0)
    else:
        addr = env_or_prompt("address", prompt_long="address or address:port of PANOS Device to configure: ")
        user = env_or_prompt("username")
        pw = env_or_prompt("password", secret=True)
        fw = Panos(addr, user, pw, debug=args.debug)
        t = fw.get_type()

        skillet = sc.get_skillet(t.lower())
        context = create_context(args.config)
        skillet.template(context)
        snippets = skillet.select_snippets(args.snippetstack, args.snippetnames)
        if len(snippets) == 0:
            print("{}Snippets {} not found for device type {}.{}".format(Fore.RED, ",".join(args.snippetnames), t,
                                                                         Style.RESET_ALL))

        for snippet in skillet.select_snippets(args.snippetstack, args.snippetnames):
            print("Doing {} at {}...".format(snippet.name, snippet.rendered_xpath), end="")
            r = set_at_path(fw, snippet.rendered_xpath, snippet.rendered_xmlstr)
            check_resp(r)


def main():
    """
    Main runtime. Decides which function to break into, either push for snippet pushes or other.
    """
    # Setup argparse
    parser = argparse.ArgumentParser(description="Deploy a Skillet to a PANOS device from one of the possible repo types.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    config_arg_group = parser.add_argument_group("Configuration options")
    repo_arg_group = parser.add_argument_group("Repository options")
    selection_options = parser.add_argument_group("Selection options")
    script_options = parser.add_argument_group("Script options")

    repo_arg_group.add_argument('--repository', default="iron-skillet", metavar="repo_name", help="Name of skillet to use"
                        .format(", ".join(GIT_SKILLET_INDEX.keys())))
    repo_arg_group.add_argument('--repotype', default="git", help="Type of skillet repo. Available options are [git, api, local]")
    repo_arg_group.add_argument("--branch", help="Git repo branch to use. Use 'list' to view available branches.")
    repo_arg_group.add_argument('--repopath', help="Path to repository if using local repo type")
    repo_arg_group.add_argument("--refresh", help="Refresh the cloned repository directory.", action='store_true')
    repo_arg_group.add_argument("--update", help="Update the cloned repository", action='store_true')

    config_arg_group.add_argument("--config", default="config_variables.yaml", help="Path to YAML variable configuration file.")
    script_options.add_argument("--debug", default="False", help="Enable debugging.", action='store_true')

    selection_options.add_argument("--snippetstack", default="snippets", help="Snippet stack to use. ")
    selection_options.add_argument("--print_entries", help="Print not just the snippet names, but the entries within them.", action='store_true')

    parser.add_argument("snippetnames", help="List of snippets to push by name.", nargs="*")
    args = parser.parse_args()
    # Url pull
    if args.repotype == "api":
        push_from_gcloud(args)
    # Git based pull
    else:
        push_skillets(args)

if __name__ == '__main__':
    main()
