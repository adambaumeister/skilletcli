from Remotes import Git
from skilletcli import create_context, env_or_prompt, set_at_path, check_resp
from pytest import fixture
from skilletcli import Panos
import os
import pytest

@fixture
def g():
    """
    Test fixture, the Skillet we use for all other testing.
    Iron-skillet is the most comprehensive, as such, it is used.
    """
    g = Git("https://github.com/PaloAltoNetworks/iron-skillet.git")
    g.clone("iron-skillet")
    return g

def test_build(g):
    """
    Test a skillet build based on the fixture.
    """
    sc = g.build()
    sc.print_all_skillets()

    assert len(sc.skillet_map.values()) > 0

def test_context(g):
    """
    Test the proper templating of snippets using the YAML configuration file.
    """
    sc = g.build()
    context = create_context("config_variables.yaml")
    sk = sc.get_skillet("panorama")
    sk.template(context)
    snippets = sk.select_snippets("snippets", ["device_mgt_config"])
    for snippet in snippets:
        print("{} {}".format(snippet.name, snippet.rendered_xmlstr))

    assert len(snippets) > 0

def test_select_entry(g):
    """
    Test the selection of a specific entry within a snippet.
    """
    sc = g.build()
    context = create_context("config_variables.yaml")
    sk = sc.get_skillet("panos")
    sk.template(context)
    snippets = sk.select_snippets("snippets", ["tag/Outbound"])

    assert len(snippets) == 1

def test_type_switch():
    """
    Test the PANOS type identification.
    """
    p = Panos("", "", "", connect=False)
    r = p.get_type_from_info("Panorama")
    assert r == "panorama"
    r = p.get_type_from_info("M-200")
    assert r == "panorama"
    r = p.get_type_from_info("PA-VM")
    assert r == "panos"

# Below are functions for testing individual skillets.
# This provides an interface through pytest to validate that a skillet works.
def test_iron_skillet(g):
    """
    Test the "iron-skillet" snippet
    """
    sc = g.build()
    test_stack = 'snippets'
    test_snippets = ['all']
    push_test(sc, test_stack, test_snippets)

def test_gpskillet():
    g = Git("https://github.com/adambaumeister/gpskillet.git")
    g.clone("gpskillet")
    sc = g.build()
    test_stack = 'snippets'
    test_snippets = ['all']
    push_test(sc, test_stack, test_snippets)

def push_test(sc, test_stack, test_snippets):
    """
    Given a skillet collection, pushes all snippets and uses Assert to validate they work.
    :param sc: SkilletCollection
    :return: None
    :raises: AssertionError
    """
    if not os.getenv("SKCLI_DEVICE_TEST"):
        pytest.skip("No environment to run device tests against.")
        return

    addr = os.getenv("SKCLI_ADDRESS")
    user = os.getenv("SKCLI_USERNAME")
    pw = os.getenv("SKCLI_PASSWORD")
    fw = Panos(addr, user, pw, debug=True)

    t = fw.get_type()

    skillet = sc.get_skillet(t.lower())
    skillet.template(None)
    snippets = skillet.select_snippets(test_stack, test_snippets)
    assert len(snippets) > 0

    success_count = 0
    for snippet in skillet.select_snippets(test_stack, test_snippets):
        print("Doing {} at {}...".format(snippet.name, snippet.rendered_xpath), end="")
        r = set_at_path(fw, snippet.rendered_xpath, snippet.rendered_xmlstr)
        result = check_resp(r)
        assert result
        success_count = success_count + 1

    print(success_count)
    assert success_count > 0

if __name__ == '__main__':
    test_type_switch()
