"""Client library to the fusion solar API"""

import logging
import requests
import time
from datetime import datetime
from functools import wraps
import json

from .exceptions import *

# global logger object
_LOGGER = logging.getLogger(__name__)


class PowerStatus:
    """Class representing the basic power status"""

    def __init__(
        self,
        current_power_kw: float,
        total_power_today_kwh: float,
        total_power_kwh: float,
    ):
        """Create a new PowerStatus object
        :param current_power_kw: The currently produced power in kW
        :type current_power_kw: float
        :param total_power_today_kwh: The total power produced that day in kWh
        :type total_power_today_kwh: float
        :param total_power_kwh: The total power ever produced
        :type total_power_kwh: float
        """
        self.current_power_kw = current_power_kw
        self.total_power_today_kwh = total_power_today_kwh
        self.total_power_kwh = total_power_kwh


def logged_in(func):
    """
    Decorator to make sure user is logged in.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
        except (json.JSONDecodeError, requests.exceptions.HTTPError):
            _LOGGER.info("Logging in")
            self._login()
            result = func(self, *args, **kwargs)
        return result

    return wrapper


class FusionSolarClient:
    """The main client to interact with the Fusion Solar API
    """

    def __init__(
        self, username: str, password: str, huawei_subdomain: str = "region01eu5"
    ) -> None:
        """Initialiazes a new FusionSolarClient instance. This is the main
           class to interact with the FusionSolar API.
           The client tests the login credentials as soon as it is initialized
        :param username: The username for the system
        :type username: str
        :param password: The password
        :type password: str
        :param huawei_subdomain: The FusionSolar API uses different subdomains for different regions.
                                 Adapt this based on the first part of the URL when you access your system.
        :
        """
        self._user = username
        self._password = password
        self._session = requests.session()
        self._huawei_subdomain = huawei_subdomain
        # hierarchy: company <- plants <- devices <- subdevices
        self._company_id = None

        # login immediately to ensure that the credentials are correct
        self._login()

    def log_out(self):
        """Log out from the FusionSolarAPI
        """
        self._session.get(
            url=f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/unisess/v1/logout",
            params={
                "service": f"https://{self._huawei_subdomain}.fusionsolar.huawei.com"
            },
        )

    def _login(self):
        """Logs into the Fusion Solar API. Raises an exception if the login fails.
        """
        # check the login credentials right away
        _LOGGER.debug("Logging into Huawei Fusion Solar API")

        url = f"https://{self._huawei_subdomain[8:]}.fusionsolar.huawei.com/unisso/v2/validateUser.action"
        params = {
            "decision": 1,
            "service": f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/unisess/v1/auth?service=/netecowebext/home/index.html#/LOGIN",
        }
        json_data = {
            "organizationName": "",
            "username": self._user,
            "password": self._password,
        }

        # send the request
        r = self._session.post(url=url, params=params, json=json_data)
        r.raise_for_status()

        # make sure that the login worked
        if r.json()["errorCode"]:
            _LOGGER.error(f"Login failed: {r.json()['errorMsg']}")
            raise AuthenticationException(
                f"Failed to login into FusionSolarAPI: { r.json()['errorMsg'] }"
            )

        # get the main id
        r = self._session.get(
            url=f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/rest/neteco/web/organization/v2/company/current",
            params={"_": round(time.time() * 1000)},
        )
        r.raise_for_status()
        self._company_id = r.json()["data"]["moDn"]

        # get the roarand, which is needed for non-GET requests, thus to change device settings
        r = self._session.get(
            url=f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/unisess/v1/auth/session"
        )
        r.raise_for_status()
        self._session.headers["roarand"] = r.json()[
            "csrfToken"
        ]  # needed for post requests, otherwise it will return 401

    @logged_in
    def get_power_status(self) -> PowerStatus:
        """Retrieve the current power status. This is the complete
           summary accross all stations.
        :return: The current status as a PowerStatus object
        """

        url = f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/rest/pvms/web/station/v1/station/total-real-kpi"
        params = {
            "queryTime": round(time.time() * 1000),
            "timeZone": 1,
            "_": round(time.time() * 1000),
        }

        r = self._session.get(url=url, params=params)
        r.raise_for_status()
        power_obj = r.json()

        power_status = PowerStatus(
            current_power_kw=power_obj["data"]["currentPower"],
            total_power_today_kwh=power_obj["data"]["dailyEnergy"],
            total_power_kwh=power_obj["data"]["cumulativeEnergy"],
        )

        return power_status

    @logged_in
    def get_plant_ids(self) -> list:
        """Get the ids of all available stations linked
           to this account
        :return: A list of plant ids (strings)
        :rtype: list
        """
        # get the complete object tree
        station_list = self.get_station_list()

        # get the ids
        plant_ids = [obj["dn"] for obj in station_list]

        return plant_ids

    @logged_in
    def get_station_list(self) -> list:
        """Get the list of available PV stations.

        :return: _description_
        :rtype: list
        """
        # get the complete list
        r = self._session.post(
            url=f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/rest/pvms/web/station/v1/station/station-list",
            json={
                "curPage":1,
                "pageSize":10,
                "gridConnectedTime":"",
                "queryTime": self._get_day_start_sec(),
                "timeZone":2,
                "sortId":"createTime",
                "sortDir":"DESC",
                "locale":"en_US"
            }
        )
        r.raise_for_status()

        obj_tree = r.json()

        if not obj_tree["success"]:
            raise FusionSolarException("Failed to retrieve station list")

        # simply return the original object list
        return obj_tree["data"]["list"]


    @logged_in
    def get_device_ids(self) -> dict:
        """gets the devices associated to a given parent_id (can be a plant or a company/account)
        returns a dictionary mapping device_type to device_id"""
        url = f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/rest/neteco/web/config/device/v1/device-list"
        params = {
            "conditionParams.parentDn": self._company_id,  # can be a plant or company id
            "conditionParams.mocTypes": "20814,20815,20816,20819,20822,50017,60066,60014,60015,23037",  # specifies the types of devices
            "_": round(time.time() * 1000),
        }
        r = self._session.get(url=url, params=params)
        r.raise_for_status()
        device_data = r.json()

        device_key = {}
        for device in device_data["data"]:
            device_key[device["mocTypeName"]] = device["dn"]
        return device_key

    @logged_in
    def active_power_control(self, power_setting) -> None:
        """apply active power control. 
        This can be usefull when electrity prices are
        negative (sunny summer holiday) and you want
        to limit the power that is exported into the grid"""
        power_setting_options = {
            "No limit": 0,
            "Zero Export Limitation": 5,
            "Limited Power Grid (kW)": 6,
            "Limited Power Grid (%)": 7,
        }
        if power_setting not in power_setting_options:
            raise ValueError("Unknown power setting")

        device_key = self.get_device_ids()

        url = f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/rest/pvms/web/device/v1/deviceExt/set-config-signals"
        data = {
            "dn": device_key["Dongle"],  # power control needs to be done in the dongle
            "changeValues": f'[{{"id":"230190032","value":"{power_setting_options[power_setting]}"}}]',  # 230190032 stands for "Active Power Control"
        }

        r = self._session.post(url, data=data)
        r.raise_for_status()

    @logged_in
    def get_plant_flow(self, plant_id: str) -> dict:
        """Retrieves the data for the energy flow
        diagram displayed for each plant
        :param plant_id: The plant's id
        :type plant_id: str
        :return: The complete data structure as a dict
        """
        # https://region01eu5.fusionsolar.huawei.com/rest/pvms/web/station/v1/overview/energy-flow?stationDn=NE%3D33594051&_=1652469979488
        r = self._session.get(
            url=f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/rest/pvms/web/station/v1/overview/energy-flow",
            params={"stationDn": plant_id, "_": round(time.time() * 1000)},
        )

        r.raise_for_status()
        flow_data = r.json()

        if not flow_data["success"] or not "data" in flow_data:
            raise FusionSolarException(f"Failed to retrieve plant flow for {plant_id}")

        return flow_data

    @logged_in
    def get_plant_stats(
        self, plant_id: str, query_time: int=None
    ) -> dict:
        """Retrieves the complete plant usage statistics for the current day.
        :param plant_id: The plant's id
        :type plant_id: str
        :param query_time: If set, must be set to 00:00:00 of the day the data should
                           be fetched for. If not set, retrieves the data for the 
                           current day.
        :type query_time: int
        :return: _description_
        """
        # set the query time to today
        if not query_time:
            query_time = self._get_day_start_sec()

        r = self._session.get(
            url=f"https://{self._huawei_subdomain}.fusionsolar.huawei.com/rest/pvms/web/station/v1/overview/energy-balance",
            params={
                "stationDn": plant_id,
                "timeDim": 2,
                "queryTime": query_time,
                "timeZone": 2,  # 1 in no daylight
                "timeZoneStr": "Europe/Vienna",
                "_": round(time.time() * 1000),
            },
        )
        r.raise_for_status()
        plant_data = r.json()

        if not plant_data["success"] or not "data" in plant_data:
            raise FusionSolarException(
                f"Failed to retrieve plant status for {plant_id}"
            )

        # return the plant data
        return plant_data["data"]

    def get_last_plant_data(self, plant_data: dict) -> dict:
        """Extracts the last measurements from the plant data
        The dict contains detailed information about the data of the plant.
        If "existInverter" the "productPower" is reported.
        :param plant_data: The plant's stats data returned by get_plant_stats
        """
        # make sure the object is valid
        if "xAxis" not in plant_data:
            raise FusionSolarException("Invalid plant_data object passed.")

        measurement_times = plant_data["xAxis"]

        # initialize the extracted data
        extracted_data = {}

        if plant_data["existInverter"]:
            (index, value) = self._get_last_value(plant_data["productPower"])
            if index:
                extracted_data["productPower"] = {
                    "time": measurement_times[index],
                    "value": value,
                }
            else:
                extracted_data["productPower"] = {
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "value": None,
                }

            extracted_data["totalPower"] = plant_data["totalProductPower"]
        else:
            extracted_data["productPower"] = {"time": None, "value": None}
            extracted_data["totalPower"] = None

        if plant_data["totalUsePower"] != "--":
            (index, value) = self._get_last_value(plant_data["usePower"])
            if index:
                extracted_data["usePower"] = {
                    "time": measurement_times[index],
                    "value": value,
                }
            else:
                # updated data is now
                extracted_data["usePower"] = {
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "value": None,
                }

            extracted_data["totalUsePower"] = plant_data["totalUsePower"]
            extracted_data["totalSelfUsePower"] = plant_data["totalSelfUsePower"]
            extracted_data["buyPowerRatio"] = plant_data["buyPowerRatio"]
            extracted_data["totalOnGridPower"] = plant_data["totalOnGridPower"]
        else:
            extracted_data["usePower"] = {"time": None, "value": None}
            extracted_data["totalUsePower"] = None
            extracted_data["totalSelfUsePower"] = None
            extracted_data["buyPowerRatio"] = None
            extracted_data["totalOnGridPower"] = None

        if plant_data["existEnergyStore"]:
            (index, value) = self._get_last_value(plant_data["chargePower"])
            if index:
                extracted_data["chargePower"] = {
                    "time": measurement_times[index],
                    "value": value,
                }
            else:
                # updated data is now
                extracted_data["chargePower"] = {
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "value": None,
                }
        else:
            extracted_data["chargePower"] = {"time": None, "value": None}

        # selfUsePower
        # existEnergyStore - dischargePower
        # radiationDosePower
        # chargePower
        # existMeter -
        # disGridPower
        # usePower
        # existUsePower

        return extracted_data

    def _get_last_value(self, values: list):
        """Get the last valid value from a values array where
           missing values are stored as '--'
        :param values: The list of values
        :type values: list
        :return: A Tuple with the index and value
        """
        found_value = False

        for index, value in enumerate(values):
            if value != "--":
                found_value = True

            if found_value and value == "--":
                return (index - 1, float(values[index - 1]))

        return (None, None)

    def _get_day_start_sec(self) -> int:
        """Return the start of the current day in seconds since
           epoche.

        :return: The start of the day ("00:00:00") in seconds
        :rtype: int
        """
        start_today = time.strftime("%Y-%m-%d 00:00:00", time.gmtime())
        struct_time = time.strptime(start_today, "%Y-%m-%d %H:%M:%S")
        seconds = round(time.mktime(struct_time) * 1000)

        return seconds
