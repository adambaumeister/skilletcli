from git import Repo
import os, stat, shutil
import re
from .skillet import *
import oyaml
from colorama import Fore, Back, Style
import requests

def on_rm_error( func, path, exc_info):
    # path contains the path of the file that couldn't be removed
    # let's just assume that it's read-only and unlink it.
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)

class Github:
    """
    Github remote
    Github provides a wrapper to Git instances and provides indexing/search methods.

    Usage::
        from Remotes import github
        g = Github()
        repos = g.index()
    """
    def __init__(self, topic="skillets", user="PaloAltoNetworks"):
        self.url = "https://api.github.com"
        self.topic = topic
        self.user = user
        self.search_endpoint = "/search/repositories"

    def index(self):
        """
        Retrieves the list of repositories as a list of Git instances.
        :return: [ Github.Git ]
        """
        r = requests.get(self.url + self.search_endpoint, params="q=topic:{}+user:{}".format(self.topic, self.user))
        j = r.json()
        self.check_resp(j)

        repos = []
        for i in j['items']:
            g = Git(i['clone_url'], github_info=i)
            repos.append(g)

        return repos

    def check_resp(self, j):
        if "errors" in j:
            if len(j["errors"]) > 0:
                raise RuntimeError("Github API Call failed! Github err: {}".format(j["message"]))

class Git:
    """
    Git remote

    This class provides an interface to Github repositories containing Skillets or XML snippets.
    """
    def __init__(self, repo_url, store=os.getcwd(), github_info=None):
        """
        Initilize a new Git repo object
        :param repo_url: URL path to repository.
        :param store: Directory to store repository in. Defaults to the current directory.
        :param github_info: (dict): If this object is initialized by the Github class, all the repo attributes from
        Github
        """
        if not check_git_exists():
            print("A git client is required to use this repository.")
            print("See README.md for more details.")
            exit(1)

        self.github_info = github_info
        self.repo_url = repo_url
        self.store = store
        self.Repo = None
        self.name = ""
        self.path = ""

    def clone(self, name, ow=False, update=False):
        """
        Clone a remote directory into the store.
        :param name: Name of repository
        :param ow: OverWrite, bool, if True will remove any existing directory in the location.
        :return: (string): Path to cloned repository
        """
        if not name:
            raise ValueError("Missing or bad name passed to Clone command.")

        self.update = update
        self.name = name
        path = self.store + os.sep + name
        if path == os.getcwd():
            raise ValueError("For whatever reason, path is set to the current working directory. Die so we don't break anything.")

        self.path = path

        if os.path.exists(path):
            if ow:
                prompt = "{}You have asked to refresh the repository. This will delete everything at {}. Are you sure? [Y/N] {}".format(Fore.RED, self.path, Style.RESET_ALL)
                print(prompt, end="")
                answer = input("")
                if answer == "Y":
                    shutil.rmtree(path,ignore_errors=False, onerror=on_rm_error)
                else:
                    print("{}Refresh specified but user did not agree to overwrite. Exiting.{}".format(Fore.RED, Style.RESET_ALL))
                    exit(1)
            else:
                self.Repo = Repo(path)
                if update:
                    print("Updating repository...")
                    self.Repo.remotes.origin.pull()

                return path
        else:
            print("Cloning into {}".format(path))
            self.Repo = Repo.clone_from(self.repo_url, path)

        self.path = path
        return path

    def branch(self, branch_name):
        """
        Checkout the specified branch.

        :param branch_name: Branch to checkout.
        :return: None
        """
        print("Checking out: "+branch_name)
        if self.update:
            print("Updating branch.")
            self.Repo.remotes.origin.pull()
        self.Repo.git.checkout(branch_name)

    def list_branches(self):
        """
        Get a list of remote branches.
        :return: []branch_names: List of branch names (minus remote)
        """
        branches = self.Repo.git.branch('-r').split('\n')
        branch_names = []
        for branch in branches:
            s = branch.split("/")
            branch_names.append(s[len(s)-1])
        return branch_names


    def build(self):
        """
        Build the Skillet object using the git repository.

        Must be called after clone.

        :return: SkilletCollection instance
        """
        if not self.Repo:
            self.clone(self.name)

        # The following section is all hard coded pointers to important stuff #
        #   We expect all of these files in every skillet structure to work.  #
        template_dirs = [
            self.path + os.sep + "templates",
            self.path + os.sep,
        ]
        snippet_dir_rx = "snippets|basic"

        # End static path definitions #
        # Expects the following structure
        # root/SKILLET_TYPE/SNIPPET_DIR/
        # A SkilletColleciton will be created for each SKILLET_TYPE
        # Populated with every snippet from SKILLET_TYPE/SNIPPET_DIR/
        # For a SKILLET_TYPE directory to be complete, it MUST contain a meta file for each SNIPPET_DIR

        template_dir = self.get_first_real_dir(template_dirs)
        skillet_types = self.get_type_directories(template_dir)
        sc = SkilletCollection(self.name)

        # This splits all the snippet directories into SnippetStack instances.
        # It uses the metadata 'type' to then add them to the correct skillet (usually 'panos' or 'panorama')
        for name, fp in skillet_types.items():
            snippet_stacks = self.get_snippets_in_dir(fp)
            for ss_name, ss in snippet_stacks.items():
                t = ss.metadata['type']
                sk = sc.new_skillet(t, t, ".*")
                sk.add_snippets(snippet_stacks)

        return sc

    def get_type_directories(self, template_dir):
        skillet_types = {}
        for dir in os.listdir(template_dir):
            fp = template_dir + os.sep + dir
            if not os.path.isfile(fp):
                # If dir is a valid type
                if dir in ['panos', 'panorama']:
                    skillet_types[dir] = fp
                # Otherwise, if the directory is a snippet directory default to PANOS
                elif self.is_snippet_dir(fp):
                    skillet_types['panos'] = template_dir + os.sep

        return skillet_types

    def get_first_real_dir(self, template_dirs):
        """
        Given a list of directories, return the first directory that exists in the system
        :param template_dirs (list): list of directories.
        """
        # Resolve the specified template directories to actual directories
        for template_dir in template_dirs:
            if os.path.isdir(template_dir):
                return template_dir

    def is_snippet_dir(self, fp):
        """
        Check if the directory at fp is a snippet directory
        """
        meta_file = fp + os.sep + ".meta-cnc.yaml"
        if os.path.exists(meta_file):
            return True

        return False

    def get_snippets_in_dir(self, fp):
        snippet_dirs = {}

        for dir in os.listdir(fp):
            if not os.path.isfile(dir):
                if self.is_snippet_dir(fp + os.sep + dir):
                    snippet_dirs[dir] = fp + os.sep + dir

        snippets_map = {}
        for dir_name, snippet_dir in snippet_dirs.items():
            meta_file = snippet_dir + os.sep + ".meta-cnc.yaml"
            if os.path.isfile(meta_file):
                metadata = oyaml.safe_load(open(meta_file).read())
                snippets = self.snippets_from_metafile(meta_file)
                if len(snippets) > 0:
                    ss = SnippetStack(snippets, metadata)
                    snippets_map[dir_name] = ss

        return snippets_map

    def snippets_from_metafile(self, meta_file):
        rel_dir = os.path.dirname(meta_file)
        metadata = oyaml.safe_load(open(meta_file).read())
        if "snippets" not in metadata:
            raise ValueError("Malformed metadata file: {}. Missing snippet definition.".format(meta_file))

        snippets = []

        for snippet_def in metadata["snippets"]:
            # This validates the snippet metadata contains all the required information
            if self.validate_snippet_meta(snippet_def, rel_dir):
                snippet_file = rel_dir + os.sep + snippet_def["file"]
                snippet_xpath = snippet_def["xpath"]
                xmlstr = open(snippet_file).read()
                s = Snippet(snippet_xpath, xmlstr)
                s.name = snippet_def["name"]
                s.set_metadata(metadata)
                snippets.append(s)

        return snippets

    def build_from_local(self, path):
        self.path = path
        self.Repo = "local"
        return self.build()

    def validate_snippet_meta(self, snippet_def, rel_dir):
        snippet_fields = ["file", "xpath"]
        # Validate all the required fields are there
        for sf in snippet_fields:
            if sf not in snippet_def:
                return False

        # Validate the values are valid
        snippet_file = rel_dir + os.sep + snippet_def["file"]
        if not os.path.isfile(snippet_file):
            return False

        return True

def check_git_exists():
    return shutil.which("git")
