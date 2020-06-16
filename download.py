#!/usr/bin/python
# -------------------------------------------------------------------
# - NAME:        HRRR_download.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2020-06-16
# -------------------------------------------------------------------
# - DESCRIPTION: Quick-and-dirty adaption of a GFS downloader.
# -------------------------------------------------------------------
# - EDITORIAL:   2018-10-11, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2020-06-16 12:51 on marvin
# -------------------------------------------------------------------

# List of the required parameters. Check the index file
# to see the available parameters. Always <param>:<level> where
# <param> and <level> are the strings as in the grib index file.
# Import some required packages
import sys
import os
import argparse

# Loading custom functions from the 'functions' python script
import functions

# -------------------------------------------------------------------
# Main script
# -------------------------------------------------------------------
if __name__ == "__main__":

    # Time to sleep between two requests
    from time import sleep
    sleeping_time = 2;

    # Split files into parameter-based files?
    split_files = True

    # ----------------------------
    # Parsing input args
    # ----------------------------
    parser = argparse.ArgumentParser(description="Download some HRRR data")
    parser.add_argument("--config","-c", type = str, default = "config.conf",
               help = "Name of the config file to be read. Default is 'config.conf'.")
    args = vars(parser.parse_args())

    # ----------------------------
    # Important step: Read the config file.
    # ----------------------------
    config = functions.read_config(args["config"])
    print(config)
    # No parameters?
    if len(config.params) == 0:
        raise Exception("No parameters to download! Check config file.")


    # ----------------------------
    # Load available files
    # ----------------------------
    gribfiles = functions.get_gribfiles_on_server(config)
    if len(gribfiles.get("files")) == 0:
        raise Exception("No files found on server - stop execution.")

    # ----------------------------
    # Create output directory
    # ----------------------------
    if not os.path.isdir(config.gribdir):
        try:
            os.makedirs(config.gribdir)
        except:
            raise Exception("Cannot create directory {:s}!".format(config.gribdir))


    # Looping over the different members first
    # Looping over forecast lead times
    for file in gribfiles.get("files"):

        # Check if we have the file on our local disc. If so, 
        # we do not have to process it again.
        if os.path.isfile(file.get("local")):
            print("File exists on disc, skip ...")
            continue

        # Read index file (once per forecast step as the file changes
        # with forecast step).
        idx = functions.parse_index_file(file.get("idx"))
        if idx is None:
            print("Not able to download/parse the index file. Possible reason:")
            print("problems with internet/server or the forecast is not available.")
            print("Continue and skip this one ...")
            continue

        # Read/parse index file (if possible) and identify the
        # required sections (byte-sections) for curl download.
        required = functions.get_required_bytes(idx, config.params)

        # If no messages found: continue
        if required is None or len(required) == 0:
            print("Could not find any required fields, skip ...")
            continue

        # Downloading the data
        functions.download_range(config, file.get("url"), file.get("local"), required)

        # Else post-processing the data
        print("Sleeping {:d} seconds ...".format(sleeping_time))
        sleep(sleeping_time)
























