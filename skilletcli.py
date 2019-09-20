#!/usr/bin/env python3

import os
import sys
import oyaml
import requests
from yaml.scanner import ScannerError
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError
from panos import Panos
from colorama import init as colorama_init
from panos import KeyDB
import re
from colorama import Fore, Back, Style
import getpass
import argparse
from Remotes import Git, Gcloud, Github
import json
from beautifultable import BeautifulTable

"""
skilletcli

This utility is designed as a CLI interface to PANOS configuration snippets.

It includes several packges for retrieving snippets from supported backend storage types.
"""
# SKCLI credentials cache
CREDS_FILENAME = ".skcli.json"
KEY_DB = KeyDB(CREDS_FILENAME)
# API
DEFAULT_API_URL = "https://api-dot-skilletcloud-prod.appspot.com"

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

def env_or_prompt(prompt, args, prompt_long=None, secret=False):
    k = "SKCLI_{}".format(prompt).upper()
    e = os.getenv(k)
    if e:
        return e

    if args.__dict__[prompt]:
        return args.__dict__[prompt]

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
    if args.repopath:
        api_url = args.repopath
    else:
        api_url = DEFAULT_API_URL

    gc = Gcloud(api_url)

    if len(args.snippetnames) == 0:
        print("{}New: browse the available objects via SkilletCloud: https://skilletcloud-prod.appspot.com/skillets/{}{}".format(
            Fore.GREEN, args.repository, Style.RESET_ALL))
        snippets = gc.List(args.repository)
        names = set()
        for s in snippets:
            names.add(s['name'])

        for n in names:
            print(n)

        sys.exit(0)

    # Address must be passed, then lookup keystore if it exists.
    addr = env_or_prompt("address", args, prompt_long="address or address:port of PANOS Device to configure: ")
    apikey = KEY_DB.lookup(addr)
    if not apikey:
        user = env_or_prompt("username", args)
        pw = env_or_prompt("password", args, secret=True)
        fw = Panos(addr, user=user, pw=pw, debug=args.debug, verify=args.validate)
        KEY_DB.add_key(addr, fw.key)
    else:
        fw = Panos(addr, apikey=apikey, debug=args.debug, verify=args.validate)

    t = fw.get_type()
    v = fw.get_version()

    context = create_context(args.config)
    snippets = gc.Query(args.repository, t, args.snippetstack, args.snippetnames, v, context)

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
    if args.repotype == "git":
        github = Github()
        repo_list = github.index()
        repo_url ='unset'
        repo_table = BeautifulTable()
        repo_table.set_style(BeautifulTable.STYLE_NONE)
        repo_table.column_headers = ['Repository Name', 'Description']
        repo_table.column_alignments['Repository Name'] = BeautifulTable.ALIGN_LEFT
        repo_table.column_alignments['Description'] = BeautifulTable.ALIGN_LEFT
        repo_table.left_padding_widths['Description'] = 1
        repo_table.header_separator_char = '-'
        if args.repository is None:
            print('Available Repositories are:')
            for repo in repo_list:
                repo_table.append_row([repo.github_info['name'],repo.github_info['description']])
            print(repo_table)
            exit()
        else:
            for repo in repo_list:
                if repo.github_info['name'] == args.repository:
                    repo_url = repo.github_info['clone_url']
                    break
            if repo_url is 'unset':
                print('Invalid Repository was specified. Available Repositories are:')
                for repo in repo_list:
                    repo_table.append_row([repo.github_info['name'],repo.github_info['description']])
                print(repo_table)
                exit()
        repo_name = args.repository
        g = Git(repo_url)
        g.clone(repo_name, ow=args.refresh, update=args.update)
        if args.branch is None:
            print("Branches available for "+args.repository+" are :")
            print("\n".join(g.list_branches()))
            exit()
        elif args.branch == "default":
            print("Using default branch for repository.")
        elif args.branch not in g.list_branches():
            print("Invalid Branch was choosen. Please select from below list:")
            print("\n".join(g.list_branches()))
            exit()
        else:
            g.branch(args.branch)

        sc = g.build()
    elif args.repotype == "local":
        repo_name = args.repopath
        g = Git("")
        sc = g.build_from_local(args.repopath)
    else:
        print("No other skillet types currently supported.")
        exit(1)

    if len(args.snippetnames) == 0:
        print("printing available {} snippets".format(repo_name))
        sc.print_all_skillets(elements=args.print_entries)
        sys.exit(0)
    else:
        addr = env_or_prompt("address", args, prompt_long="address or address:port of PANOS Device to configure: ")
        apikey = KEY_DB.lookup(addr)
        if not apikey:
            user = env_or_prompt("username", args)
            pw = env_or_prompt("password", args, secret=True)
            fw = Panos(addr, user=user, pw=pw, debug=args.debug, verify=args.validate)
            KEY_DB.add_key(addr, fw.key)
        else:
            fw = Panos(addr, apikey=apikey, debug=args.debug, verify=args.validate)

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
    colorama_init()

    # Setup argparse
    parser = argparse.ArgumentParser(description="Deploy a Skillet to a PANOS device from one of the possible repo types.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    config_arg_group = parser.add_argument_group("Configuration options")
    repo_arg_group = parser.add_argument_group("Repository options")
    selection_options = parser.add_argument_group("Selection options")
    script_options = parser.add_argument_group("Script options")
    kdb_options = parser.add_argument_group("Keystore options")

    repo_arg_group.add_argument('--repository', default="iron-skillet", help="Name of skillet to use. Use without a value to see list of all available repositories.", nargs='?')
    repo_arg_group.add_argument('--repotype', default="git", help="Type of skillet repo. Available options are [git, api, local]")
    repo_arg_group.add_argument("--branch", default="default", help="Git repo branch to use. Use without a value to view all available branches.",nargs='?')
    repo_arg_group.add_argument('--repopath', help="Path to repository if using local repo type")
    repo_arg_group.add_argument("--refresh", help="Refresh the cloned repository directory.", action='store_true')
    repo_arg_group.add_argument("--update", help="Update the cloned repository", action='store_true')

    config_arg_group.add_argument("--config", default="config_variables.yaml", help="Path to YAML variable configuration file.")
    script_options.add_argument("--debug", help="Enable debugging.", action='store_true')
    script_options.add_argument("--validate", help="Enable certificate validation on all endpoints.", action='store_true')
    script_options.add_argument("--username", help="Firewall/Panorama username. Can also use envvar SKCLI_USERNAME.")
    script_options.add_argument("--address", help="Firewall/Panorama address. Can also use envvar SKCLI_ADDRESS")
    script_options.add_argument("--password", help="Firewall/Panorama login password. Can also use envvar SKCLI_PASSWORD")
    kdb_options.add_argument("--clear_keystore", help="Remove all stored apikeys.", action='store_true')
    kdb_options.add_argument("--enable_keystore", help="Enable the storage of API keys.", action='store_true')

    selection_options.add_argument("--snippetstack", default="snippets", help="Snippet stack to use. ")
    selection_options.add_argument("--print_entries", help="Print not just the snippet names, but the entries within them.", action='store_true')

    parser.add_argument("snippetnames", help="List of snippets to push by name.", nargs="*")
    args = parser.parse_args()

    if not args.validate:
        print("""{}Warning: SSL validation of PANOS device is currently disabled. Use --validate to enable it.{}""".format(Fore.YELLOW, Style.RESET_ALL))
        requests.packages.urllib3.disable_warnings()

    if args.enable_keystore:
        print("""{}API keys will be saved, per device, at {}.{}""".format(
            Fore.MAGENTA, KEY_DB.path, Style.RESET_ALL)
        )

        KEY_DB.enable()

    if args.clear_keystore:
        KEY_DB.reinit()

    # Url pull
    if args.repotype == "api":
        push_from_gcloud(args)
    # Git based pull
    else:
        push_skillets(args)

if __name__ == '__main__':
    main()
