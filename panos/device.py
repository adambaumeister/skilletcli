from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError
from urllib3.exceptions import ProtocolError
import requests
import re
class Panos:
    """
    PANOS Device class.

    Represents either a firewall or panorama and provides a minimal interface to run commands.
    """
    def __init__(self, addr, apikey=None, user="admin", pw=None, connect=True, debug=False, verify=False):
        """
        Initialize a new panos object
        :param addr: NAME:PORT combination (ex. l72.16.0.1:443)
        :param user: username
        :param pw: password
        :param connect (true): Specify whether to connect at init or not.
        """
        self.type_switch = {
            r'panorama': "panorama",
            r'm-': "panorama",
        }

        self.verify = verify

        self.url = "https://{}/api".format(addr)
        self.user = user
        self.pw = pw
        self.key = ''
        if debug == True:
            self.log_level = 1
        else:
            self.log_level = 0

        self.log("Logging level is {}".format(self.log_level))
        if apikey:
            self.key = apikey
            return

        if connect:
            self.connect()


    def connect(self):
        """
        Connect to a PANOS device and retrieve an API key.
        :return: API Key
        """
        params = {
            "type": "keygen",
            "user": self.user,
            "password": self.pw,
        }
        self.log("Connecting to {}".format(self.url))
        r = self.send(params)
        if not self.check_resp(r):
            print("Error on login received from PANOS: {}".format(r.text))
            exit(1)

        root = ElementTree.fromstring(r.content)
        elem = root.findall("./result/key")
        self.key = elem[0].text
        return self.key

    def send(self, params):
        """
        Send a request to this PANOS device
        :param params: dict: POST parameters for query ({ "type": "op" })
        :return: GET Response type
        """
        url = self.url
        params["key"] = self.key
        self.log("{} : {}".format(url, params), level=2)
        try:
            # = requests.get(url, params=params, verify=False)
            r = requests.post(url, data=params, verify=self.verify)
        except ProtocolError:
            print("Failed to send a rqequest.")
            exit(1)
        return r

    def get_type(self):
        """
        Get the type of PANOS device using show system info

        :param panos: PANOS device object
        :return:
        """
        params = {
            "type": "op",
            "cmd": "<show><system><info></info></system></show>"
        }
        self.log("Sending: {}".format(params))

        r = self.send(params)
        if not self.check_resp(r):
            print("Error on login received from PANOS: {}".format(r.text))
            exit(1)

        self.log(r.content)
        root = ElementTree.fromstring(r.content)

        # Get the device type
        elem = root.findall("./result/system/model")
        t = elem[0].text
        type_result = self.get_type_from_info(t)

        # Get the device version
        elem = root.findall("./result/system/sw-version")
        self.sw_version = elem[0].text
        self.major_sw_version = ".".join(self.sw_version.split(".")[0:2])
        self.log("Device details: {}:{} {} {}".format(type_result, t, self.sw_version, self.major_sw_version))

        return type_result

    def get_version(self):
        if not self.major_sw_version:
            self.get_type()

        return self.major_sw_version

    def get_type_from_info(self, t):
        for regex, result in self.type_switch.items():
            if re.search(regex, t.lower()):
                return result

        return "panos"

    def log(self, l, level=1):
        if level <= self.log_level:
            print(l)

    def check_resp(self, r):
        try:
            root = ElementTree.fromstring(r.content)
        except ParseError as e:
            print(r.content)
            print("{}".format(e))
            exit(1)

        status = root.attrib["status"]
        if status == "success":
            return True
        else:
            return False