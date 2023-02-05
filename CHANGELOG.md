# 0.0.11

  * Improved documentation of returned values
  * Improved `get_last_plant_data` to include all available values

# 0.0.10

  * Added additional values to `get_last_plant_data`

# 0.0.9

  * Adapted `get_last_plant_data` to return `float` instead of strings

# 0.0.8

  * Fixed bugs that prevented meter data to be correctly added to the plant stats
  * Added additional combined statistics to the plant stats
  * Updated the README to show new features

# 0.0.7

  * Added a new function `get_station_list` that returns detailed info about all installed
    stations under that account.
  * Changed the functionality of `get_plant_ids` to only return the ids of stations. In some
    setups, the ids returned here are ids of subunits (ie. dongle) that can't be used to extract
    further information.

# 0.0.6

  * Fixed a bug in `get_plant_stats`: Query time was by default set to the current time.
    But the API expects this to be 00:00:00 of the current day.