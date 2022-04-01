from unittest import TestCase
import logging
import json
import os

from fusion_solar.client import FusionSolarClient
from fusion_solar.exceptions import *


class FusionSolarClientTest(TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.DEBUG)

        # load the credentials
        cred_filename = os.path.join(os.path.dirname(__file__), "credentials.json")

        if not os.path.exists(cred_filename):
            raise Exception("Tests require a 'credentials.json' file in the 'tests' directory. "
                            "This file must contain a dict with a 'username' and 'password' which "
                            "which are used to test the HuaweiFusionSolar API.")

        # load the file
        with open(cred_filename, "r") as reader:
            cred_data = json.load(reader)

            if "username" not in cred_data or "password" not in cred_data:
                raise Exception("Invalid 'credentials.json' file. Must contain 'username' and 'password.")

            self.user = cred_data["username"]
            self.password = cred_data["password"]

    def test_login(self):
        # create a new client instance
        # TODO: Remove real username and password
        client = FusionSolarClient(self.user, self.password)

    def test_failed_login(self):
        self.assertRaises(AuthenticationException, FusionSolarClient, "asda", "asda")

    def test_status(self):
        client = FusionSolarClient(self.user, self.password)

        status = client.get_power_status()

        self.assertIsNotNone(status.current_power_kw)
