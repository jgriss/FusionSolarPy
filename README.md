[![Test Package](https://github.com/jgriss/FusionSolarPy/actions/workflows/test.yaml/badge.svg)](https://github.com/jgriss/FusionSolarPy/actions/workflows/test.yaml)
[![PyPI version](https://badge.fury.io/py/fusion_solar_py.svg)](https://badge.fury.io/py/fusion_solar_py)

# FusionSolarPy

A very basic python client for the HuaweiFusionSolar API used to monitor
solar power plants.

This client uses the https://region01eu5.fusionsolar.huawei.com end point by default. It is
possible to change this using the `huawei_subdomain` parameter. But this has not
been tested on any other end-points.

Please report any bugs!

## Installation

Simply install from pypi using:

```bash
pip install fusion_solar_py
```

By default, libraries required for solving CAPTCHAs are not installed. To also install
these requirements, use the command:

```bash
pip install fusion_solar_py[captcha]
```

Note that these require python >= 3.8

## Usage

The basic usage centers around the `FusionSolarClient` class. It currently
only has one method to extract the current power production, the total
power production for the current day, and the total energy ever produced
by the plant.

```python
from fusion_solar_py.client import FusionSolarClient

# log into the API - with proper credentials...
client = FusionSolarClient("my_user", "my_password")

# NOTE: Depending on your region, you may need to set the
# `huawei_subdomain` parameter. This is the first part of the
# URL when you enter the FusionSolar API through your webbrowser
#
# client = FusionSolarClient("my_user", "my_password", huawei_subdomain="region01eu5")

# get the stats
stats = client.get_power_status()

# print all stats
print(f"Current power: {stats.current_power_kw} kW")
print(f"Total energy today: {stats.energy_today_kwh} kWh")
print(f"Total energy: {stats.energy_kwh} kWh")

# log out - just in case
client.log_out()
```

It is additional possible to retrieve the data for specific
plants - in case multiple plants are available through the
account.

```python
from fusion_solar_py.client import FusionSolarClient

# log into the API - with proper credentials...
client = client = FusionSolarClient(
  "my_user",
  "my_password",
  huawei_subdomain="subdomain"
)


# get the plant ids
plant_ids = client.get_plant_ids()

print(f"Found {len(plant_ids)} plants")

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
print(f"Total produced power (today): {last_values['totalPower']} kWh")
print(f"Produced power consumed (today): {last_values['totalSelfUsePower']} kWh")
print(f"Relative amount of used power bought from grid: {last_values['buyPowerRatio']}%")

# print all optimizer stats
for x in client.get_optimizer_stats(client.get_device_ids()['Inverter']):
    print(f"{x['optName']}: {x['moStatus']} {x['runningStatus']}: {x['outputPower']} W /" +
          f" {x['inputVoltage']} V / {x['inputCurrent']} A / {x['temperature']} C")


# log out - just in case
client.log_out()
```

### New uni000 subdomains

It seems that some accounts are currently being moved to a new version of the web application. These can be recognized by the new "uni...eu5" subdomain (f.e. `uni002eu5`).

This new version apparently requires a new login procedure which is supported since version 0.0.19. Yet, it is unclear whther the Captcha solving also still works. Finally, other features may be affected as well. Therefore, in case your account was moved to a "uni..." subdomain and you experience issues, please post a respective [Issue](https://github.com/jgriss/FusionSolarPy/issues).

### Captcha solving

Sometimes, if logging in too often, the API will return a captcha. If you let your script run continuously, you shouldn't run into this issue. In case you rerun the script often, providing a captcha solver resolves this issue.

By default, the requirements to solve CAPTCHAs are not insalled. To install them, use

```bash
pip install fusion_solar_py[captcha]
```

Note that these require python >= 3.8

#### Simple usage
1. Download the weights of the captcha solver [captcha_huawei.onnx](models/captcha_huawei.onnx) and save it somewhere you can find it again.
2. Pass the path to the weights to the client in the `captcha_model_path` parameter.

```python
from fusion_solar_py.client import FusionSolarClient

client = FusionSolarClient(
    'my_user',
    'my_password',
    captcha_model_path="C:/Users/user/models/captcha_huawei.onnx"
)
```
By default, the captcha solver will use the CPU for inference, which should be fast enough (~200ms). If you want to use the GPU, please refer to the [onnx documentation](https://onnxruntime.ai/docs/execution-providers/) on how to install the necessary packages.
You can pass the device configuration via the `captcha_device` parameter.

Example:
```python
from fusion_solar_py.client import FusionSolarClient

# Using GPU if available, otherwise CPU
client = FusionSolarClient(
    'my_user',
    'my_password',
    captcha_model_path="C:/Users/user/models/captcha_huawei.onnx",
    captcha_device=['CUDAExecutionProvider', 'CPUExecutionProvider']
)
```

### Session reuse

In case you have to reestablish the connection to the API many times (e.g. for usage with Telegraf), you might want to reuse the session. This can be done by passing the `session` parameter to the client. The session needs to be a `requests.Session` object. If you don't pass a session, a new one will be created.
Reusing a session will significantly reduce the chance of getting a captcha, since the API counts logins, not hits for rate limiting.

```python
import requests
import pickle
from fusion_solar_py.client import FusionSolarClient

session = requests.Session()
client = FusionSolarClient(
    'my_user',
    'my_password',
    session=session
)

# To save the session for later use (e.g. if you have to run the script multiple times), you can use pickle and save the session to the disk
with open('session.pkl', 'wb') as f:
    pickle.dump(session, f)

# To load the session, you can use pickle again
with open('session.pkl', 'rb') as f:
    session = pickle.load(f)
```

## Available plant data / stats

This is a list of variables and a (guessed) explanation of what they mean returnd from
`get_plant_stats` and as an abbreviated version by `get_last_plant_data`.

### Total values

These values are always the total (in kWh) for the current day:

  * **totalSelfUsePower**: Total kWh of the current day's production used.
  * **selfProvide**: Total kWh of the current day's production used (same as above).
  * **totalBuyPower**: Total kWh bought from the grid today.
  * **totalProductPower**: Total kWh produced by the PV today.
  * **totalUsePower**: Total kWh used today.
  * **totalOnGridPower**: Total kWh returned to the grid today.

### Ratios

Ratios are given in percent (f.e. "35.93" for a ratio of 0.3593)

  * **onGridPowerRatio**: Proportion of today's PV production returned to the grid.
  * **buyPowerRatio**: Proportion of power consumed today that was bought from the grid.
  * **selfUsePowerRatioByProduct**: Proportion of produced power used.

### Logicals

  * **existInverter**: (Boolean) Set if an inverter (ie a PV plant) is installed
  * **existCharge**: (Boolean) - Maybe true if currently charging.
  * **existMeter**: (Boolean) Set if a meter is installed.
  * **existEnergyStore**: (Boolean) - Maybe true if a storage is installed.
  * **existUsePower**: (Boolean) - Maybe true if the own power is used.

### Timecourses

These are returned as lists of values. The matching timepoints are found in the
`xAxis` list. `get_last_plant_data` returns these values as a dict with the key
`time` and `value` representing the last valid measurement (ie. not "--").

  * **selfUsePower**: Amount of energy produced by the PV used.
  * **dischargePower**: Amounf of energy discharged from the storage.
  * **chargePower**: Amount of energy charged into the storage.
  * **onGridPower**: (Probably) The amount of power returned to the grid.
  * **disGridPower**: (Probably) The amount of power taken from the grid.
  * **productPower**: Amounf of power produced by the PV.
  * **usePower**: Amount of power used.

## Available battery stats

### [get_battery_ids(plant_id)](src/fusion_solar_py/client.py#L417)

This function returns a list of battery IDs from the given plant. The returned battery ID is used for the other battery functions.

### [get_battery_basic_stats(battery_id)](src/fusion_solar_py/client.py#L433)

This function returns a `BatteryStatus` object. It takes the information from [get_battery_status(battery_id)](#get_battery_status(battery_id)) and just provides an easy wrapper, similar to [get_power_status()](src/fusion_solar_py/client.py#L325). It contains the following information:

* **`rated_capacity`**: The total capacity of the battery in kWh
* **`operating_status`**: The current operating status of the battery
* **`backup_time`**: The time the battery can run on its own (we think - our battery doesn't have this value)
* **`bus_voltage`**: The current bus voltage in V
* **`total_charged_today_kwh`**: The total amount of energy charged today in kWh
* **`total_discharged_today_kwh`**: The total amount of energy discharged today in kWh
* **`current_charge_discharge_kw`**: The current charge/discharge power in kW


### [get_battery_day_stats(battery_id)](src/fusion_solar_py/client.py#L454)

This function returns a list of dicts, where each dict is a timestamp. Each dict is 5 minutes apart. It contains **charge/discharge power** and **state of charge (SOC)**
<details>
<summary>Example output</summary>

```python
{
    '30005': {
        'pmDataList': [
            {
                'counterId': 30005,
                'counterValue': -0.262,  # Negative means discharge, positive means charge
                'dnId': 123456,  # Battery ID
                'dstOffset': 60,
                'period': 300,
                'startTime': 1694988000,  # UNIX timestamp
                'timeZoneOffset': 60
            },
            ...
        ],
        'total': int,
        'name': 'Charge/Discharge power'
    },
    '30007': {
        'pmDataList': [
            {
                'counterId': 30007,
                'counterValue': 56.0,  # SOC in %
                'dnId': 123456,  # Battery ID
                'dstOffset': 60,
                'period': 300,
                'startTime': 1694988000,  # UNIX timestamp
                'timeZoneOffset': 60
            },
            ...
        ],
        'total': int,
        'name': 'SOC'
    }
}
```
</details>

### [get_battery_module_stats(battery_id, module_id="1", signal_ids=None)](src/fusion_solar_py/client.py#L486)

This function retrieves the complete stats for the given battery module of the latest recorded time. It returns a list of dicts. For the details of the dicts, please see [signals.md](signals.md)


### [get_battery_status(battery_id)](src/fusion_solar_py/client.py#L528)

This function retrieves the current status of the battery. It returns a list of dicts. We haven't figured out the meaning of all the modes yet.

* **Battery operating status**
* **Charge/Discharge mode**
* **Rated capacity**: Probably the total capacity of the battery in kWh
* **Backup time**: Probably the time the battery can run on its own
* **Energy charged today**: The total amount of energy charged today in kWh
* **Energy discharged today**: The total amount of energy discharged today in kWh
* **Charge/Discharge power**: The current charge/discharge power in kW
* **Bus voltage**: The current bus voltage in V
* **SOC**: The current state of charge in %

<details>
  <summary>Example output</summary>

```python
[
    {
        'id': 10003,
        'latestTime': 1695047841,
        'name': 'Battery operating status',
        'realValue': '2',
        'unit': '',
        'value': 'Operating'
    },
    {
        'id': 10008,
        'latestTime': 1695047841,
        'name': 'Charge/Discharge mode',
        'realValue': '4',
        'unit': '',
        'value': 'Maximum self-consumption'
    },
    {
        'id': 10013,
        'latestTime': 1695062404,
        'name': 'Rated capacity',
        'realValue': '5.000',
        'unit': 'kWh',
        'value': '5.000'
    },
    {
        'id': 10015,
        'latestTime': 1695062404,
        'name': 'Backup time',
        'realValue': 'N/A',
        'unit': 'min',
        'value': '-'
    },
    {
        'id': 10001,
        'latestTime': 1695062404,
        'name': 'Energy charged today',
        'realValue': '3.72',
        'unit': 'kWh',
        'value': '3.72'
    },
    {
        'id': 10002,
        'latestTime': 1695062404,
        'name': 'Energy discharged today',
        'realValue': '4.83',
        'unit': 'kWh',
        'value': '4.83'
    },
    {
        'id': 10004,
        'latestTime': 1695062404,
        'name': 'Charge/Discharge power',
        'realValue': '-0.485',
        'unit': 'kW',
        'value': '-0.485'
    },
    {
        'id': 10005,
        'latestTime': 1695062404,
        'name': 'Bus voltage',
        'realValue': '766.7',
        'unit': 'V',
        'value': '766.7'
    },
    {
        'id': 10006,
        'latestTime': 1695062404,
        'name': 'SOC',
        'realValue': '31.0',
        'unit': '%',
        'value': '31.0'
    }
]
```
</details>

