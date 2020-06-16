

Quick and dirty script to download HRRR forecasts (grib files).
Kind of a Frankenstein script, patched together from various other
functions I wrote at some point to get something 'close to running' :).

Developed on Python version `3.6.9`.

Greez
R

# Requirements

Requires some python packages.

* Standard libraries.
* `numpy`
* `pycurl`: for downloading data.
* `bs4` (BeautifulSoup): parse available files on webserver.


# Rough outline

1. import `functions` (`functions.py`) which contains the custom functions.
2. Parse input arguments.
3. Parse configuration file; can be set via input arguments.
4. `get_gribfiles_on_server()`: Find available files on the servers by reading the FTP/HTTP inventory.
    Only returns information for the files matching the configuration.
5. Looping over the files from the previous step:
    1. Read the grib2 index file (`*.idx`) from the server.
    2. `parse_index_file()`: Parse the file, extract required information such
       as parameter name, level and forecast step.
    3. `get_required_bytes()`: based on the grib2 inventory (index file from previous
        step) and the parameter configuration in the config file: search for
        grib2 messages matching the parameters defined in the config file and return
        the required byte ranges to be downloaded.
    4. `download_range()`: Download the segments/byte ranges defined in the previous
        step (i.e., download specific grib messages).

# Usage

```
python download.py [--config config.conf]
```

# Configuration

See comments in the configuration file `config.conf`. Can be used as a template,
the argument `--config` allows to specify different config files for different
tasks.

# Output

The data will be stored as `grib2` with the same naming/structure as on the
server - but subsetted according to the configuration file. 

