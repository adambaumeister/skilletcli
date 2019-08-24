from pathlib import Path
import os
import json


class KeyDB:
    """
    Maintains a mapping of Device to Apikey in the users home directory.
    Usage::
        kdb = Keystore("filename")
        kdb.enable()
        kdb.add_key("index","apikey")
        key = kdb.lookup("index")
    """
    def __init__(self, fn):
        self.filename = fn
        self.enabled = False
        self.keys = {}
        self.get_creds_file()

    def enable(self):
        """
        Enable the keystore for use.
        """
        self.enabled = True

    def get_creds_file(self):
        """
        Get all keys from the credentials file.
        Also configures this instance with all of the keys.
        :return: (dict): Index: keys mapping
        """
        filename = self.filename

        home = str(Path.home())
        filepath = home + os.sep + filename
        self.path = filepath
        if not os.path.isfile(filepath):
            return False

        j = json.load(open(filepath))
        self.keys = j
        return j

    def lookup(self, device):
        """
        Lookup a single key from the store by index
        :param device: (string): Index
        :return: Key value
        """
        if device in self.keys:
            return self.keys[device]

    def add_key(self, device, key):
        """
        Add a single key to the store
        :param device: (string): Index
        :param key: (string): Key value
        """
        if not self.enabled:
            return
        self.keys[device] = key
        fh = open(self.path, "w")
        json.dump(self.keys, fh)
        fh.close()
        os.chmod(self.path, 0o600)

    def reinit(self):
        """
        Obliterate all keys in the store and reset permissions.
        Does not delete the keystore file.
        """
        self.keys = {}
        fh = open(self.path, "w")
        json.dump(self.keys, fh)
        fh.close()
        os.chmod(self.path, 0o600)