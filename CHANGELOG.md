# 0.0.6

  * Fixed a bug in `get_plant_stats`: Query time was by default set to the current time.
    But the API expects this to be 00:00:00 of the current day.