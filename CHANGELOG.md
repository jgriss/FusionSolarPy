# 0.0.26

  * Added support for the new `roarand` header which is required for several function calls.

# 0.0.25

  * Added support for the new encrypted login function introduced in API version 3

# 0.0.24

  * Added new function `get_current_plant_data`

# 0.0.23

  * Added new functions `is_session_active` and `keep_alive`
  * Adapted the @logged_in wrapper to use this new function

# 0.0.22

  * Fixed detection of incorrect subdomains
  * Added test for session reuse
  * Removed deprecation decorators from PowerStatus as these clashed with @property 
    decorators (functions will still be removed in the future)

# 0.0.21

  * Fixed bug in handling session configuration in new login procedure.

# 0.0.20

  * Added support for new login procedure in "unixxx" subdomains.

# 0.0.14

  * Fixed login issue with subdomain "intl"

# 0.0.13

  * Added function `get_optimizer_stats` to retrieve optimizer data (thanks to @Miouge1)

# 0.0.12

  * Explicitly catch incorrect subdomain

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