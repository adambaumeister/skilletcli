import requests
import os
"""
To use this test suite in dev, first start Flask.

To test against a real environment, use the envvar TEST_URL.

This test suite uses the "iron-skillet" skillet as test data. As such, you must have uploaded it using skupload.py before
this suite will work.
"""

TEST_URL="http://127.0.0.1:5000"
if os.getenv("TEST_URL"):
    TEST_URL = os.getenv("TEST_URL")
# A working, valid query for a "tag" snippet
TEST_SNIPPET_TAG_QUERY = {
  "skillet": "iron-skillet",
  "filters": {
    "name": [
      "tag"
    ],
    "type": "panos",
    "stack": "snippets"
  },
  "template_variables": {}
}
# A broken query (missing template_variable IPV6_SINKHOLE) for an "address" snippet
TEST_SNIPPET_ADDRESS_QUERY = {
  "skillet": "iron-skillet",
  "filters": {
    "name": [
      "address"
    ],
    "type": "panos",
    "stack": "snippets"
  },
  "template_variables": {
      "IPV4_SINKHOLE": "127.0.0.1"
  }
}

def test_search():
    # Test search functionality
    res = requests.get(TEST_URL +"/search?skillet=iron-skillet&search=address&type=panorama")
    j = res.json()
    for s in j:
       print(s['name'], s['path'], s['stack'], s['type'], s['template_variables'])
    assert len(j) >= 1


def test_get_snippets():
    # Test a basic snippet query using a POST
    res = requests.post(TEST_URL+"/snippet", json=TEST_SNIPPET_TAG_QUERY)
    j = res.json()
    assert len(j) == 1
    assert "xml" in j[0]


def test_get_collections():
    # Test the retrevial of the collection index
    res = requests.get(TEST_URL)
    j = res.json()
    assert len(j) >= 1


def test_list_snippets():
    # Test a listing of all the snippets
    res = requests.get(TEST_URL +"/snippet?skillet=iron-skillet")
    j = res.json()
    assert len(j) >= 1


def test_broken_snippet_list():
    # Test the API responds correctly to a malformed query
    # In this case, omit the required variable "skillet"
    res = requests.get(TEST_URL +"/snippet")
    j = res.json()
    assert "result" in j
    assert j["result"] == "error"


def test_broken_snippet_query():
    # Test a basic snippet query using a POST
    res = requests.post(TEST_URL+"/snippet", json=TEST_SNIPPET_ADDRESS_QUERY)
    j = res.json()
    assert "result" in j
    assert j["result"] == "error"


if __name__ == "__main__":
    test_search()
    test_list_snippets()
    test_get_snippets()
    test_get_collections()
    test_broken_snippet_list()
    test_broken_snippet_query()