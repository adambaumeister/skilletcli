import requests
import os
"""
To use this test suite in dev, first start Flask.
"""
TEST_URL="http://127.0.0.1:5000"
if os.getenv("TEST_URL"):
    TEST_URL = os.getenv("TEST_URL")

TEST_SNIPPET_QUERY = {
    "skillet": "iron-skillet",
    "filters": {
        "name": ["shared_address", "shared_tag"],
        "type": "panorama",
        "stack": "snippets",
    },
    "template_variables": {
        "SINKHOLE_IPV4": "1.1.1.1",
        "SINKHOLE_IPV6": "::1",
    }
}
def test_get_snippets():
    res = requests.post(TEST_URL+"/snippet", json=TEST_SNIPPET_QUERY)
    print(res.json())

def test_get_collections():
    res = requests.get(TEST_URL)
    print(res.json())

def test_list_snippets():
    res = requests.get(TEST_URL +"/snippet?skillet=iron-skillet")
    print(res.json())

if __name__ == "__main__":
    test_list_snippets()
    test_get_snippets()
    test_get_collections()