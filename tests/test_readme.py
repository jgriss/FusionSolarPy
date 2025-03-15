## This test case simulates the examples given in the README file
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

class ReadmeTest(TestCase):
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
        
    def test_example_1(self):
        client = FusionSolarClient(self.user, self.password, self.subdomain, captcha_model_path=self.captcha_model_path)

        # get the stats
        stats = client.get_power_status()

        # print all stats
        print(f"Current power: {stats.current_power_kw} kW")
        print(f"Total energy today: {stats.energy_today_kwh} kWh")
        print(f"Total energy: {stats.energy_kwh} kWh")

        # NOTE: Since an update of the API, this data does no longer seem
        #       to be up-to-date. The most recent data only seems to be
        #       available on th plant level (see below)

        # log out - just in case
        client.log_out()
    
    def test_example_2(self):
        client = FusionSolarClient(self.user, self.password, self.subdomain, captcha_model_path=self.captcha_model_path)

        # if you only need an overview of the current status of
        # your plant(s) you can use the get_plant_list function
        plant_overview = client.get_station_list()

        # get the current power of your first plant
        print(f"Current power production: { plant_overview[0]['currentPower'] }")

        # alternatively, you can get time resolved data for each plant:

        # get the plant ids
        plant_ids = client.get_plant_ids()

        print(f"Found {len(plant_ids)} plants")

        # get the basic (current) overview data for the plant
        plant_overview = client.get_current_plant_data(plant_ids[0])

        print(str(plant_overview))

        # get the data for the first plant
        plant_data = client.get_plant_stats(plant_ids[0])

        # plant_data is a dict that contains the complete
        # usage statistics of the current day. There is
        # a helper function available to extract some
        # most recent measurements
        last_values = client.get_last_plant_data(plant_data)

        print(f"Last production at {last_values['productPower']['time']}: {last_values['productPower']['value']}")

        # In case you have a battery installed
        print(f"Last battery charge at {last_values['chargePower']['time']}: {last_values['chargePower']['value']}")

        # Additionally, if you have a meter installed you can get additional statistics
        print(f"Total power consumption (today): {last_values['totalUsePower']} kWh")
        print(f"Total produced power (today): {last_values['totalProductPower']} kWh")
        print(f"Produced power consumed (today): {last_values['totalSelfUsePower']} kWh")
        print(f"Relative amount of used power bought from grid: {last_values['buyPowerRatio']}%")

        # print all optimizer stats
        device_ids = client.get_device_ids()
        inverters= list(filter(lambda e: e['type'] == 'Inverter', device_ids))
        for inverter in inverters:
            try:
                for x in client.get_optimizer_stats(inverter['deviceDn']):
                    print(f"{x['optName']}: {x['moStatus']} {x['runningStatus']}: {x['outputPower']} W /" +
                        f" {x['inputVoltage']} V / {x['inputCurrent']} A / {x['temperature']} C")
            except FusionSolarException as e:
                # This happens if there are not optimizers present
                print(f"No opimitizer available for {inverter['deviceDn']}")


        # log out - just in case
        client.log_out()

