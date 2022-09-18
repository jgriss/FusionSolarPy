# 0.0.7

  * Added a new function `get_station_list` that returns detailed info about all installed
    stations under that account.
  * Changed the functionality of `get_plant_ids` to only return the ids of stations. In some
    setups, the ids returned here are ids of subunits (ie. dongle) that can't be used to extract
    further information.

# 0.0.6

  * Fixed a bug in `get_plant_stats`: Query time was by default set to the current time.
    But the API expects this to be 00:00:00 of the current day.