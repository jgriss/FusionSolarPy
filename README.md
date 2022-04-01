# FusionSolarPy

A very basic python client for the HuaweiFusionSolar API used to monitor
solar power plants.

This client is currently hard-coded to use the https://region01eu5.fusionsolar.huawei.com end point and has not
been tested on any other end-points.

## Installation

Simply install from pypi using:

```bash
pip install fusion_solar
```

## Usage

The basic usage centers around the `FusionSolarClient` class. It currently
only has one method to extract the current power production, the total
power production for the current day, and the total energy ever produced
by the plant.

```python
from fusion_solar.client import FusionSolarClient

# log into the API - with proper credentials...
client = FusionSolarClient("my_user", "my_password")

# get the stats
stats = client.get_power_status()

# print all stats
print(f"Current power: {stats.current_power_kw} kW")
print(f"Total power today: {stats.total_power_today_kwh} kWh")
print(f"Total power: {stats.total_power_kwh} kWh")

# log out - just in case
client.log_out()
```