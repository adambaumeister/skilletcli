import argparse
from Remotes import Git
from web.db import Firestore

def main():
    """
    Main runtime. Decides which function to break into, either push for snippet pushes or other.
    """
    # Setup argparse
    parser = argparse.ArgumentParser(description="Deploy and administer skillets in gcloud firestore", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    script_options = parser.add_argument_group("Script options")

    repo_arg_group = parser.add_argument_group("Repository options")

    script_options.add_argument("--debug", default="False", help="Enable debugging.", action='store_true')
    script_options.add_argument("--rebuild_meta", default="False", help="Reinitalize the document schema", action='store_true')
    repo_arg_group.add_argument('--repository', default="iron-skillet", metavar="repo_name", help="Name of skillet to use")
    repo_arg_group.add_argument('--repotype', default="git", help="Type of skillet repo")
    repo_arg_group.add_argument("--branch", help="Git repo branch to use. Use 'list' to view available branches.")
    repo_arg_group.add_argument('--repopath', help="Path to repository if using local repo type")
    repo_arg_group.add_argument("--refresh", help="Refresh the cloned repository directory.", action='store_true')
    repo_arg_group.add_argument("--update", help="Update the cloned repository", action='store_true')
    args = parser.parse_args()

    firestore = Firestore(debug=args.debug)

    repo_name = args.repository
    repo_url = args.repopath
    g = Git(repo_url)
    g.clone(repo_name, ow=args.refresh, update=args.update)
    if args.branch:
        if args.branch == "list":
            print("\n".join(g.list_branches()))
            exit()
        g.branch(args.branch)

    sc = g.build()
    if args.rebuild_meta:
        firestore.rebuild()
    firestore.AddSkilletCollection(sc)

if __name__ == '__main__':
    main()
