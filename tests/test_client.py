from unittest import TestCase
import logging
import json
import os
import sys
import requests

currentdir = os.path.dirname(__file__)
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, os.path.join(parentdir, "src")) 

from fusion_solar_py.client import FusionSolarClient
from fusion_solar_py.exceptions import *


class FusionSolarClientTest(TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.DEBUG)

        # disable logging for urllib
        logging.getLogger("urllib3").setLevel(logging.ERROR)

        # setup the captcha solver
        self.captcha_model_path = os.path.join(os.path.dirname(__file__), "..", "models", "captcha_huawei.onnx") 

        # load the credentials
        cred_filename = os.path.join(os.path.dirname(__file__), "credentials.json")

        if os.path.exists(cred_filename):
            # load the file
            with open(cred_filename, "r") as reader:
                cred_data = json.load(reader)

                if "username" not in cred_data or "password" not in cred_data:
                    raise Exception("Invalid 'credentials.json' file. Must contain 'username' and 'password.")

                self.user = cred_data["username"]
                self.password = cred_data["password"]
                self.subdomain = cred_data.get('subdomain', "region01eu5")
        # check if the credentials are available as environment variables (GitHub actions)
        elif os.environ["TEST_USER"]:
            self.user = os.environ.get("TEST_USER")
            self.password = os.environ.get("TEST_PASSWORD")
            self.subdomain = "region01eu5"
        else:
            raise Exception("Tests require a 'credentials.json' file in the 'tests' directory. "
                            "This file must contain a dict with a 'username' and 'password' which "
                            "which are used to test the HuaweiFusionSolar API.")      

    def test_login(self):
        # create a new client instance
        client = FusionSolarClient(self.user, self.password, self.subdomain, captcha_model_path=self.captcha_model_path)

        # ensure the loging worked by checking the keep alive data
        payload = client.keep_alive()

        self.assertIsNotNone(payload)

    def test_failed_login(self):
        self.assertRaises(AuthenticationException, FusionSolarClient, "asda", "asda")

    def test_status(self):
        client = FusionSolarClient(self.user, self.password, self.subdomain)

        status = client.get_power_status()

        self.assertIsNotNone(status.current_power_kw)

    def test_current_plant_data(self):
        client = FusionSolarClient(self.user, self.password, self.subdomain)

        plant_ids = client.get_plant_ids()

        current_plant_data = client.get_current_plant_data(plant_ids[0])

        self.assertIsNotNone((current_plant_data))
        self.assertTrue(current_plant_data["yearEnergy"] > 0)

    def test_get_plant_stats(self):
        client = FusionSolarClient(self.user, self.password, self.subdomain)

        plant_ids = client.get_plant_ids()

        self.assertIsInstance(plant_ids, list)
        self.assertTrue(len(plant_ids) > 0)

        self.assertRaises(requests.exceptions.HTTPError, client.get_plant_stats, "1234")

        plant_stats = client.get_plant_stats(plant_ids[0])

        self.assertIsNotNone(plant_stats)

        with open("/tmp/plant_data.json", "w") as writer:
            json.dump(plant_stats, writer, indent=3)

        # get the last measurements
        last_data = client.get_last_plant_data(plant_stats)

        self.assertIsNotNone(last_data["productPower"])

        with open("/tmp/last_data.json", "w") as writer:
            json.dump(last_data, writer, indent=3)

        # get the energy flow data structure
        energy_flow = client.get_plant_flow(plant_id=plant_ids[0])

        self.assertIsNotNone(energy_flow)

        with open("/tmp/plant_flow.json", "w") as writer:
            json.dump(energy_flow, writer, indent=3)

        # get the device ids
        device_ids = client.get_device_ids()

        self.assertTrue(len(device_ids) > 0)
        inverters = list(filter(lambda e: e['type'] == 'Inverter', device_ids))
        self.assertTrue(len(inverters) > 0)
        inverter_id = inverters[0]['deviceDn']
        self.assertIsNotNone(inverter_id)

        # test optimizer data
        try:
            optimizer_data = client.get_optimizer_stats(inverter_id=inverter_id)
        except FusionSolarException as e:
            self.assertEqual(str(e), f"Failed to retrieve optimizer status for {inverter_id}")

    def test_get_station_list(self):
        client = FusionSolarClient(self.user, self.password, self.subdomain)

        station_list = client.get_station_list()

        self.assertIsInstance(station_list, list)
        self.assertTrue(len(station_list) > 0)

        with open("/tmp/station_list.json", "w") as writer:
            json.dump(station_list, writer, indent=3)

    def test_get_battery_stats(self):
        client = FusionSolarClient(self.user, self.password, self.subdomain)

        # get the plant ids
        plant_ids = client.get_plant_ids()

        # get the stats
        battery_ids = client.get_battery_ids(plant_id=plant_ids[0])

        # to enable tests on systems without batteries
        if len(battery_ids) < 1:
            return

        battery_id = battery_ids[0]

        battery_day_stats = client.get_battery_day_stats(battery_id)

        self.assertIsInstance(battery_day_stats, dict)

        battery_stats = client.get_battery_module_stats(battery_id)

        self.assertIn("30005", battery_stats)
        self.assertIn("30007", battery_stats)

        battery_rt_stats = client.get_battery_status(battery_id)

        self.assertIsInstance(battery_rt_stats, dict)

    def test_incorrect_subdomain(self):
        self.assertRaises(AuthenticationException, FusionSolarClient, self.user, self.password, "region04eu5")

    def test_session_reuse(self):
        session = requests.Session()

        client = FusionSolarClient(self.user, self.password, self.subdomain, session=session)

        stats = client.get_power_status()

        self.assertIsNotNone(stats)
        plant_ids = client.get_plant_ids()

        # create a second client using the session
        client2 = FusionSolarClient(self.user, self.password, self.subdomain, session=session)

        stats2 = client2.get_power_status()

        self.assertIsNotNone(stats2)

    def test_session_active(self):
        client = FusionSolarClient(self.user, self.password, self.subdomain)

        # now the session should be fine
        self.assertTrue(client.is_session_active())

        # add an invalid session object
        client = FusionSolarClient(self.user, self.password, self.subdomain, session=requests.Session())

        self.assertFalse(client.is_session_active())        

    def test_keep_alive(self):
        client = FusionSolarClient(self.user, self.password, self.subdomain)

        payload = client.keep_alive()

        self.assertIsNotNone(payload)
