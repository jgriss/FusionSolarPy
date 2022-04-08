"""Client library to the fusion solar API"""

import logging
import requests
import time
import simplejson
from datetime import datetime
from fusion_solar_py.exceptions import *

# global logger object
_LOGGER = logging.getLogger(__name__)


class PowerStatus:
    """Class representing the basic power status"""

    def __init__(self, current_power_kw: float, total_power_today_kwh: float, total_power_kwh: float):
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


class FusionSolarClient:
    """The main client to interact with the Fusion Solar API
    """

    def __init__(self, username: str, password: str) -> None:
        """Initialiazes a new FusionSolarClient instance. This is the main
           class to interact with the FusionSolar API.

           The client tests the login credentials as soon as it is initialized

        :param username: The username for the system
        :type username: str
        :param password: The password
        :type password: str
        """
        self._user = username
        self._password = password
        self._session = None
        self._parent_id = None

        # login immediately to ensure that the credentials are correct
        self._login()

    def _is_logged_in(self) -> bool:
        """Checks whether we are currently logged in

        :return: Boolean indicatin whether we're logged in
        :rtype: bool
        """
        login_data = self._send_request(
            url="https://region01eu5.fusionsolar.huawei.com/unisess/v1/auth/session")

        return isinstance(login_data, dict)

    def log_out(self):
        """Log out from the FusionSolarAPI
        """
        self._send_request("https://region01eu5.fusionsolar.huawei.com/unisess/v1/logout",
                           {"service": "https://region01eu5.fusionsolar.huawei.com"})

    def _login(self):
        """Logs into the Fusion Solar API. Raises an exception if the login fails.
        """
        # check the login credentials right away
        _LOGGER.debug("Logging into Huawei Fusion Solar API")

        url = "https://eu5.fusionsolar.huawei.com/unisso/v2/validateUser.action"

        params = {
            "decision": 1,
            "service": "https://region01eu5.fusionsolar.huawei.com/unisess/v1/auth?service=/netecowebext/home/index.html#/LOGIN"
        }
        json_data = {"organizationName": "",
                     "username": self._user, "password": self._password}

        # send the request
        login_response = self._send_request(url, params, json_data)

        # make sure that the login worked
        if login_response["errorCode"]:
            _LOGGER.error(f"Login failed: {login_response['errorMsg']}")
            raise AuthenticationException(
                f"Failed to login into FusionSolarAPI: { login_response['errorMsg'] }")

        # get the main id
        main_obj = self._send_request(
            url="https://region01eu5.fusionsolar.huawei.com/rest/neteco/web/organization/v2/company/current",
            params={"_": round(time.time() * 1000)})

        self._parent_id = main_obj["data"]["moDn"]

    def _send_request(self, url: str, params: dict = None, data: dict = None) -> dict:
        """Sends a request to the specified URL with the parameters.
           Immediately tests whether the request was successfull, otherwise
           an exception is thrown.

        :param url: The URL to contact
        :type url: str
        :param params: The parameters as a dict, defaults to None
        :type params: dict, optional
        :param data: If set, this data will be send as JSON encoded data in a POST request
        :type data: dict, optional
        :return: The resulting JSON object
        :rtype: dict
        """
        # create the session object in case it does not exist
        if not self._session:
            self._session = requests.session()

        # submit the request
        if data:
            response = self._session.post(url=url, params=params, json=data)
        else:
            response = self._session.get(url=url, params=params)

        if response.status_code != 200:
            raise RequestException(
                f"HTTP request failed: {response.status_code}")

        # extract the JSON data
        try:
            json_data = response.json()

            return json_data
        except simplejson.errors.JSONDecodeError:
            return response.content.decode()
        except Exception as e:
            raise RequestException(f"Failed to convert JSON data: {e}")

    def get_power_status(self) -> PowerStatus:
        """Retrieve the current power status. This is the complete
           summary accross all stations.

        :return: The current status as a PowerStatus object
        :rtype: PowerStatus
        """
        if not self._is_logged_in():
            self._login()

        url = "https://region01eu5.fusionsolar.huawei.com/rest/pvms/web/station/v1/station/total-real-kpi"
        params = {
            "queryTime": round(time.time()) * 1000,
            "timeZone": 1,
            "_":  time.time() * 1000
        }

        power_obj = self._send_request(url, params)

        power_status = PowerStatus(
            current_power_kw=power_obj["data"]["currentPower"],
            total_power_today_kwh=power_obj["data"]["dailyEnergy"],
            total_power_kwh=power_obj["data"]["cumulativeEnergy"]
        )

        return power_status

    def get_plant_ids(self) -> list:
        """Get the ids of all available plants linked
           to this account

        :return: A list of plant ids (strings)
        :rtype: list
        """
        # get the complete object tree
        obj_tree = self._send_request(
            url="https://region01eu5.fusionsolar.huawei.com/rest/neteco/web/organization/v2/tree", params={
                "parentDn": self._parent_id,
                "self": "true",
                "companyTree": "false",
                "cond": '{"BUSINESS_DEVICE":1,"DOMAIN":1}',
                "pageId": 1,
                "_": round(time.time() * 1000)}
        )

        # get the ids
        plant_ids = [obj["elementDn"] for obj in obj_tree[0]["childList"]]

        return plant_ids

    def get_plant_stats(self, plant_id: str) -> dict:
        """Retrieves the complete plant usage statistics for the current day.

        :param plant_id: The plant's id
        :type plant_id: str
        :return: _description_
        :rtype: dict
        """
        try:
            plant_data = self._send_request(
                url="https://region01eu5.fusionsolar.huawei.com/rest/pvms/web/station/v1/overview/energy-balance",
                params={
                    "stationDn": plant_id,
                    "timeDim": 2,
                    "queryTime": round(time.time()) * 1000,
                    "timeZone": 2,  # 1 in no daylight
                    "timeZoneStr": "Europe/Vienna",
                    "_": round(time.time() * 1000)

                })
        except FusionSolarException as err:
            raise FusionSolarException(
                f"Failed to retrieve plant status for {plant_id}. Please verify the plant id.")

        if not plant_data["success"] or not "data" in plant_data:
            raise FusionSolarException(f"Failed to retrieve plant status for {plant_id}")

        # return the plant id
        return plant_data["data"]

    def get_last_plant_data(self, plant_data: dict) -> dict():
        """Extracts the last measurements from the plant data

        The dict contains detailed information about the data of the plant.
        If "existInverter" the "productPower" is reported.

        :param plant_data: The plant's stats data returned by get_plant_stats
        :type plant_data: dict
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
                extracted_data["productPower"] = {"time": measurement_times[index], "value": value}
            else:
                extracted_data["productPower"] = {"time": datetime.now().strftime("%Y-%m-%d %H:%M"), "value": None}
        else:
            extracted_data["productPower"] = {"time": None, "value": None}

        if plant_data["existUsePower"]:
            (index, value) = self._get_last_value(plant_data["usePower"])
            if index:
                extracted_data["usePower"] = {"time": measurement_times[index], "value": value}
            else:
                # updated data is now
                extracted_data["usePower"] = {"time": datetime.now().strftime("%Y-%m-%d %H:%M"), "value": None}
        else:
            extracted_data["usePower"] = {"time": None, "value": None}

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
