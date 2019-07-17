from git import Repo
import os, stat, shutil
import re
from .skillet import *
import oyaml
from colorama import Fore, Back, Style

def on_rm_error( func, path, exc_info):
    # path contains the path of the file that couldn't be removed
    # let's just assume that it's read-only and unlink it.
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)

class Git:
    """
    Git remote

    This class provides an interface to Github repositories containing Skillets or XML snippets.
    """
    def __init__(self, repo_url, store=os.getcwd()):
        """
        Initilize a new Git repo object
        :param repo_url: URL path to repository.
        :param store: Directory to store repository in. Defaults to the current directory.
        """
        if not check_git_exists():
            print("A git client is required to use this repository.")
            print("See README.md for more details.")
            exit(1)
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
        :return:
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
        print("Checking out: "+branch_name)
        if self.update:
            print("Updating branch.")
            self.Repo.remotes.origin.pull()
        self.Repo.git.checkout(branch_name)

    def build(self):
        """
        Build the Skillet object using the git repository.
        :return:
        """
        if not self.Repo:
            self.clone(self.name)

        # The following section is all hard coded pointers to important stuff #
        #   We expect all of these files in every skillet structure to work.  #
        template_dirs = [
            self.path + os.sep + "templates"
        ]
        snippet_dir_rx = "snippets.*"

        # End static path definitions #

        skillet_types = {}
        # Expects the following structure
        # root/SKILLET_TYPE/SNIPPET_DIR/
        # A SkilletColleciton will be created for each SKILLET_TYPE
        # Populated with every snippet from SKILLET_TYPE/SNIPPET_DIR/
        # For a SKILLET_TYPE directory to be complete, it MUST contain a meta file for each SNIPPET_DIR

        # Here we pull all the SKILLET_TYPES
        for template_dir in template_dirs:
            for dir in os.listdir(template_dir):
                fp = template_dir + os.sep + dir
                if not os.path.isfile(fp):
                    skillet_types[dir] = fp

        sc = SkilletCollection()
        # Now we extract the SNIPPET_DIRS
        for name, fp in skillet_types.items():
            sk = sc.new_skillet(name, name, ".*")
            snippets = self.get_snippets_in_dir(fp, snippet_dir_rx)
            sk.add_snippets(snippets)

        return sc

    def get_snippets_in_dir(self, fp, snippet_dir_rx):
        snippet_dirs = {}
        for dir in os.listdir(fp):
            if not os.path.isfile(dir):
                if re.search(snippet_dir_rx, dir):
                    snippet_dirs[dir] = fp + os.sep + dir

        snippets_map = {}
        for dir_name, snippet_dir in snippet_dirs.items():
            meta_file = snippet_dir + os.sep + ".meta-cnc.yaml"
            if os.path.isfile(meta_file):
                snippets_map[dir_name] = self.snippets_from_metafile(meta_file)

        return snippets_map

    def snippets_from_metafile(self, meta_file):
        rel_dir = os.path.dirname(meta_file)
        metadata = oyaml.safe_load(open(meta_file).read())
        if "snippets" not in metadata:
            raise ValueError("Malformed metadata file: {}. Missing snippet definition.".format(meta_file))

        snippets = []
        for snippet_def in metadata["snippets"]:
            snippet_file = rel_dir + os.sep + snippet_def["file"]
            snippet_xpath = snippet_def["xpath"]
            if os.path.isfile(snippet_file):
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

def check_git_exists():
    return shutil.which("git")
