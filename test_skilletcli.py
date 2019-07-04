from Remotes import Git
from skilletcli import create_context
from pytest import fixture

@fixture
def g():
    g = Git("https://github.com/PaloAltoNetworks/iron-skillet.git")
    g.clone("iron-skillet")
    return g

def test_build(g):
    sc = g.build()
    sc.print_all_skillets()

    assert len(sc.skillet_map.values()) > 0

def test_context(g):
    sc = g.build()
    context = create_context("config_variables.yaml")
    sk = sc.get_skillet("panorama")
    sk.template(context)
    snippets = sk.select_snippets("snippets", ["device_mgt_config"])
    for snippet in snippets:
        print("{} {}".format(snippet.name, snippet.rendered_xmlstr))

    assert len(snippets) > 0

def test_select_entry(g):
    sc = g.build()
    context = create_context("config_variables.yaml")
    sk = sc.get_skillet("panos")
    sk.template(context)
    snippets = sk.select_snippets("snippets", ["tag/Outbound"])

    assert len(snippets) == 1
