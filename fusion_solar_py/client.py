"""Client library to the fusion solar API"""

import logging
import requests
import time
import simplejson
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

        # login immediately to ensure that the credentials are correct
        self._login()

    def _is_logged_in(self) -> bool:
        """Checks whether we are currently logged in

        :return: Boolean indicatin whether we're logged in
        :rtype: bool
        """
        login_data = self._send_request(url="https://region01eu5.fusionsolar.huawei.com/unisess/v1/auth/session")

        return isinstance(login_data, dict)

    def log_out(self):
        """Log out from the FusionSolarAPI
        """
        self._send_request("https://region01eu5.fusionsolar.huawei.com/unisess/v1/logout", {"service": "https://region01eu5.fusionsolar.huawei.com"})

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
        json_data = {"organizationName":"","username":self._user,"password":self._password}

        # send the request
        login_response = self._send_request(url, params, json_data)

        # make sure that the login worked
        if login_response["errorCode"]:
            _LOGGER.error(f"Login failed: {login_response['errorMsg']}")
            raise AuthenticationException(f"Failed to login into FusionSolarAPI: { login_response['errorMsg'] }")
        
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
            raise RequestException(f"Failed to contact login site ({response.status_code}")

        # extract the JSON data
        try:
            json_data = response.json()

            return json_data
        except simplejson.errors.JSONDecodeError:
            return response.content.decode()
        except Exception as e:
            raise RequestException(f"Failed to convert JSON data: {e}")

    def get_power_status(self) -> PowerStatus:
        """Retrieve the current power status.

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

