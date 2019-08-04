import requests
"""
To use this test suite in dev, first start Flask.
"""
TEST_URL="http://127.0.0.1:5000"
TEST_SNIPPET_QUERY = {
    "skillet": "iron-skillet",
    "filters": {
        "name": "shared_address",
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

if __name__ == "__main__":
    test_get_snippets()
    #test_get_collections()