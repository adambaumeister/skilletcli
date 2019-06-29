from Remotes import Git
from create_and_push import create_context

def test_git_clone():
    g = Git("https://github.com/adambaumeister/iron-skillet.git")
    g.clone("iron-skillet")

def test_build():
    g = Git("https://github.com/adambaumeister/iron-skillet.git")
    g.clone("iron-skillet")
    sc = g.build()
    sc.print_all_skillets()

    assert len(sc.skillet_map.values() > 0)

def test_context():
    g = Git("https://github.com/adambaumeister/iron-skillet.git")
    g.clone("iron-skillet")
    sc = g.build()
    context = create_context("config_variables.yaml")
    sk = sc.get_skillet("panorama")
    sk.template(context)
    snippets = sk.select_snippets("snippets", "device_mgt_config")
    for snippet in snippets:
        print("{} {}".format(snippet.name, snippet.rendered_xmlstr))

    assert len(snippets) > 0

test_context()