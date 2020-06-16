# -------------------------------------------------------------------
# - NAME:        functions.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2020-06-16
# -------------------------------------------------------------------
# - DESCRIPTION: Set of functions used by download.py
# -------------------------------------------------------------------
# - EDITORIAL:   2020-06-16: Adaption of a GFS downloader ...
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2020-06-16 12:09 on marvin
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
class get_gribfiles_on_server:

    def __init__(self, config):

        self.config = config

        # Download folders on server
        from urllib.request import urlopen
        try:
            data = urlopen(self.config.url).read()
        except Exception as e:
            raise Exception(e)

        # Find all folders
        from bs4 import BeautifulSoup
        root = BeautifulSoup(data, "html.parser")

        from re import match
        self.files = []
        for node in root.find_all("a"):
            tmp_dir = match(r"^(hrrr.[0-9]{8})\/?$", node.text)
            if tmp_dir:
                tmp_dir     = tmp_dir.group(1).replace("/$", "")
                self.files += self._get_files(tmp_dir)

    # Standard representation of this object
    def __repr__(self):

        res = "Summary of \"get_gribfiles_on_server\" object:\n\n"
        if len(self.files) == 0:
            res += "- No files found on server\n"
        else:
            res += "{:10s} {:7s} {:30s}  {:10s}   {:4s}  {:5s}".format(
                   "dir", "domain", "filename", "type", "rh", "step")
            for f in self.files: print(f)
            for f in self.files: res += str(f) + "\n"
        return res


    def _get_files(self, dir):
        """_get_files(dir)

        Parameters
        ==========
        dir : str
            Name of the directory on the server.

        Returns
        =======
        Based on the URL and the domain (see config), the directory specified
        will be checked for all available files matching a specific pattern
        ("^hrrr\..*\.grib2$"; all grib2 files). A list with 'gribfile' objects
        will be returned or an empty list if no matching files can be found.
        """

        from re import match
        from bs4 import BeautifulSoup
        from urllib.request import urlopen

        url = "{:s}/{:s}/{:s}/".format(self.config.url, dir, self.config.domain)
        data = urlopen(url)

        result = []
        root = BeautifulSoup(data, "html.parser")
        for node in root.find_all("a"):
            if match(r"^hrrr\..*\.grib2$", node.text):
                tmp = gribfile(self.config, dir, node.text)
                if tmp.get("step") in self.config.steps and \
                   tmp.get("runhour") in self.config.runhours:
                       result.append(tmp)

        return result

    def get(self, what):
        """get(what)

        Parameters
        ==========
        what : str
            name of the attribute to be returned

        Returns
        =======
        If the attribute on the object is found, the attribute is returned.
        Else an error will be raised.
        """
        try:
            x = getattr(self, what)
        except:
            raise Error("whoops, \"{:s}\" attribute not found.".format(what))
        return x 

# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
class gribfile:
    """gribfile(config, file)

    Parameters
    ==========
    config : ...
        ...
    file : string
        name of the grib file on the server
    """

    def __init__(self, config, dir, file):

        self.file   = file
        self.dir    = dir
        self.domain = config.domain
        self.url    = "{:s}/{:s}/{:s}/{:s}".format(config.url, dir, config.domain, file)
        self.idx    = self.url + ".idx" # Index file

        # Extracting runhour, type, and forecast step
        from re import match
        tmp = match(r"^hrrr\.t([0-9]+)z\.([a-z]+)([0-9]+)\.grib2$", file)
        self.runhour = int(tmp.group(1))
        self.type    = tmp.group(2)
        self.step    = int(tmp.group(3))

        # Append local file name
        import os
        self.local   = os.path.join(config.gribdir, dir, config.domain, file)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        #        dir  domain   file    type   runhour   step
        return "{:10s} {:7s} {:30s}  {:10s}   {:2d}Z  +{:3d}h".format(
                self.get("dir"), self.get("domain"),
                self.get("file"), self.get("type"), self.get("runhour"), self.get("step"))

    def get(self, what):
        """get(what)

        Parameters
        ==========
        what : str
            name of the attribute to be returned

        Returns
        =======
        If the attribute on the object is found, the attribute is returned.
        Else an error will be raised.
        """
        try:
            x = getattr(self, what)
        except:
            raise Error("whoops, \"{:s}\" attribute not found.".format(what))
        return x 



# -------------------------------------------------------------------
# -------------------------------------------------------------------
def get_param_file_name(filedir, date, step, param):
    """get_param_file_name(filedir, date, step, param)

    Generates the parameter-based file name.

    Parameters
    ----------
    filedir : str
        folder where to store the downloaded files
    date : datetime.datetime
        defines model initialization date and time
    step : int
        forecast step (in hours)
    param : str
        shortname of the parameter

    Returns
    -------
    Returns a string, file name of the local parameter-based file.
    This is used to check if the files exist and to split the "full" grib file
    into single parameter-based grib files.
    """
    import os
    import datetime as dt
    from numpy import int64
    if not isinstance(filedir, str):
        raise ValueError("filedir has to be a string")
    if not isinstance(step, int) and not isinstance(step, int64):
        raise ValueError("step has to be an integer")
    if not isinstance(param, str):
        raise ValueError("param has to be a string")

    # Local file names
    tmp = date.strftime("GFS_%Y%m%d_%H00")
    return {"local"  : os.path.join(filedir, "{:s}_f{:03d}_{:s}.grb2".format(tmp, step, param)),
            "subset" : os.path.join(filedir, "{:s}_f{:03d}_{:s}_subset.grb2".format(tmp, step, param))}


# -------------------------------------------------------------------
# -------------------------------------------------------------------
class index_entry(object):

    def __init__(self, args):
        """index_entry(args)

        A small helper class to handle index entries.
        
        Parameters
        ----------
        args : dict
            dict with the extracted entries from the index file (row-by-row).

        Details
        -------
        With the use of a regular expression the different elements of each
        line in the index file are extracted and put into a dictionary.
        This dictionary is the input for this function and requires to at least
        include the 'required' elements ["byte", "date", "param", "level", "step"].
        """

        from re import sub

        if not type(args) == dict:
            raise ValueError("Input 'args' must be a dictionary")
        required = ["byte_start", "date", "param", "level", "step"]
        if not all(key in args for key in required):
            raise ValueError("Not all required elements in 'args'.")

        self._byte_start = int(args["byte_start"])
        self._byte_end   = False
        self._var        = str(args["param"])
        self._step       = str(args["step"])
        # Replace brackets for level
        self._lev        = str(args["level"])
        self._lev        = sub("(\(|\)|\[|\]|\{|\})", "", self._lev)


    def add_end_byte(self, x):
        """add_end_byte(x)

        Appends the ending byte.
        """
        self._byte_end = x

    def end_byte(self):
        """end_byte()

        Returns end byte.
        """
        try:
            x = getattr(self, "_byte_end")
        except:
            raise Error("whoops, _byte_end attribute not found.")
        return x 

    def start_byte(self):
        """start_byte()

        Returns start byte.
        """
        try:
            x = getattr(self, "_byte_start")
        except:
            raise Error("whoops, _byte_start attribute not found.")
        return x 

    def key(self):
        """key()

        Returns
        -------
        Returns a character string "<param name>:<param level>:<step info>"
        as shown in the index file. Used to identify messages (in combination
        with the expressions in the config file).
        """
        try:
            var  = getattr(self, "_var")
            lev  = getattr(self, "_lev")
            step = getattr(self, "_step")
        except Exception as e:
            raise Exception(e)

        return "{:s}:{:s}:{:s}".format(var, lev, step)

    def duration(self):
        """duration()

        Returns
        -------
        A character string or None. If string, the string is
        of the following form "Xh TTT" where
        X ([0-9]+) is the duration/period in hours, TTT the type of
        measure. As an example, 6 hour accumulated precipitation will
        return a duration-string "6h acc". If no period/duration is found
        (forecasted value/message is the current value) None will be
        returned.
        """
        from re import match
        # Searching for the pattern "10-11" or similar. If found,
        # the duration will be calculated. Else 'None' will be returned
        # (instant/current value).
        tmp = match("^(\d+)-(\d+)\s(\w+).*$", self._step)
        if not tmp: return None
        tmp = dict(zip(["from", "to", "unit"], tmp.groups()))
        
        if tmp["unit"] == "hour":
            duration = int(tmp["to"]) - int(tmp["from"])
        else:
            raise Exception("Don't know how to handle 'duration' for unit '{:s}'".format(tmp["unit"]))

        return duration

    def step(self):
        """step()

        Returns
        -------
        Message forecast step.
        """
        from re import match
        # Range? Take second
        tmp = match("^\d+-(\d+)\s\w+.*$", self._step)
        if tmp:
            return int(tmp.group(1))
        # Instant/current value?
        tmp = match("^(\d+)\s(\w+).*$", self._step)
        if tmp and tmp.group(2) == "hour":
            return int(tmp.group(1))

        # Else break
        raise Exception("Don't know how to deal with '{:s}'.".format(self._step))

    def range(self):
        """range()

        Returns
        -------
        Returns the byte range for curl.
        """
        try:
            start = getattr(self, "_byte_start")
            end   = getattr(self, "_byte_end")
        except Exception as e:
            raise Exception(e)
        end = "" if end is None else "{:d}".format(end)

        return "{:d}-{:s}".format(start, end)

    def __repr__(self):
        if isinstance(self._byte_end, bool):
            end = "UNKNOWN"
        elif self._byte_end is None:
            end = "end of file"
        else:
            end = "{:d}".format(self._byte_end)
        return "IDX ENTRY: {:10d}-{:>10s}, '{:s}' (+{:d}h; {:s})".format(self._byte_start,
                end, self.key(), self.step(),
                "current value" if self.duration() is None else str(self.duration()))

# -------------------------------------------------------------------
# -------------------------------------------------------------------
def parse_index_file(idxfile, remote = True):
    """parse_index_file(idxfile, remote = True)
 
    Downloading and parsing the grib index file.
    Can be used to read local and remote (http/https) index files.

    Parameters
    ----------
    idxfile : str
        url to the index file
    remote : bool
        if remote = True urllib2 is used to read the file from the
        web, else expected to be a local file.

    Returns
    -------
    Returns a list of index entries (entries of class index_entry).
    """

    if remote:

        from urllib.request import urlopen
        try:
            data = urlopen(idxfile).read()
        except Exception as e:
            print("[!] Problems reading index file\n    {:s}\n    ... return None".format(idxfile))
            return None

        data = data.decode("utf-8")

    else:
        from os.path import isfile
        if not isfile(idxfile):
            raise Exception("file {:s} does ont exist on disc".format(idxfile))
        with open(idxfile, "r") as fid:
            data = "".join(fid.readlines())

    if len(data) == 0:  return None
    else:               data = data.split("\n")
       

    # List to store the required index message information
    idx_entries = []

    # Parsing data (extracting message starting byte,
    # variable name, and variable level)
    from re import compile, findall
    #                    byte      date    param      level       step
    comp = compile("^\d+:(\d+):d=(\d{10}):([^:.?]+):([^:\\..?]*):(.*?):$")
    comp_keys = ["byte_start", "date", "param", "level", "step"]
    byte = 1 # initial byte
    for line in data:
        if len(line) == 0: continue
        mtch = findall(comp, line.replace(".", "-"))
        if not mtch:
            raise Exception("whoops, pattern mismatch \"{:s}\"".format(line))
        # Else crate the index_entry (object of class index_entry which takes up
        # the information from the index file)
        idx_entries.append(index_entry(dict(zip(comp_keys, mtch[0]))))

    # Now we know where the message start (bytes), but we do not
    # know where they end. Append this information.
    for k in range(0, len(idx_entries)):
        if (k + 1) == len(idx_entries):
            idx_entries[k].add_end_byte(None)
        else:
            idx_entries[k].add_end_byte(idx_entries[k+1].start_byte() - 1)

    # Go trough the entries to find the messages we request for.
    #for rec in idx_entries: print(rec)
    return idx_entries


# -------------------------------------------------------------------
# -------------------------------------------------------------------
def create_index_file(grbfile):
    """parse_index_file(grbfile):
 
    Well, this is not very efficient. If I cannot find the index file
    on the server (happens every now and then) I am simply downloading
    the grib2 file if existing, create my own index file, and use
    this index file. However, at this point I already have a local
    copy of the grib2 file and I could use this rather than downloading
    via curl once again. But ... TODO.

    Parameters
    ----------
    grbfile : str
        url of the remote grib2 file.

    Returns
    -------
    Either None if the grib2 file does not exist (in this case we
    cannot create an index file locally) or what parse_index_file returns.
    """

    # Requires wgrib2: check if existing
    import distutils.spawn
    check = distutils.spawn.find_executable("wgrib2")
    if not check: 
        print("[!] Creating index file on your own does not work (wgrib2 missing), skip.")
        return None

    # Import library
    try:
        from urllib import urlretrieve # Python 2
    except ImportError:
        from urllib.request import urlretrieve # Python 3

    import tempfile
    tmp1 = tempfile.NamedTemporaryFile(prefix = "GFS_grib_")
    tmp2 = tempfile.NamedTemporaryFile(prefix = "GFS_idx_")
    try:
        urlretrieve(grbfile, tmp1.name)
    except:
        return None
    
    import subprocess as sub
    import os
    #print(tmp1.name)
    #print(grbfile)
    os.system("wgrib2 {:s}".format(tmp1.name))
    p = sub.Popen(["wgrib2", tmp1.name],
                  stdout = sub.PIPE, stderr = sub.PIPE)
    out, err = p.communicate()

    if not p.returncode == 0:
        print("[!] Not able to create proper index file in create_index_file, return None")
        return None

    with open(tmp2.name, "w") as fid: fid.write(out)

    idx = parse_index_file(tmp2.name, remote = False)
    tmp1.close()
    tmp2.close()
      
    # Return list
    return idx



# -------------------------------------------------------------------
# -------------------------------------------------------------------
def get_required_bytes(idx, params, stopifnot = False):
    """get_required_bytes(idx, params, stopifnot = False)

    Searching for the entries in idx corresponding to the parameter
    definition in params (has to match the grib2 inventory param names, e.g.,
    "TMP:2 m surface"). Returns a list of bytes which have to be downloaded
    with curl later on.

    Parameter
    ---------
    idx : list
        list of index_entry objects. The list returned by parse_index_file.
    params : dict
        parameter configuration from the config file.
    stopifnot : bool
        stop if one (or several) parameters cannot be found in the index
        file. If set to false these messages will simply be ignored.

    Returns
    -------
    Returns a list of bytes (for curl).
    """

    from re import match
    from numpy import int64

    # Crate a list of the string if only one string is given.
    if not isinstance(params, dict):
        raise ValueError("params has to be a dictionary")

    # Go trough the entries to find the messages we request for.
    res     = []
    found   = []
    missing = []
    for x in idx:
        count = 0
        for param,ppattern in params.items():
            if match(ppattern, x.key()): count = count + 1
        if count == 1:
            res.append(x.range())
            found.append(x.key())
        elif count > 0:
            raise Exception("Expression \"{:s}\" matches multiple entries in the index file!".format(
                            x.key()))
        else: # count == 0
            missing.append(param)

    # Go trough the entries to find the messages we request for.
    res     = []
    found   = []
    missing = []
    for param,ppattern in params.items():
        count = 0
        msg_found = None
        for x in idx:
            if match(ppattern, x.key()):
                count = count + 1
                msg_found = x # Leep this message
        if count == 1:
            res.append(msg_found.range())
            found.append(msg_found.key())
        elif count > 0:
            raise Exception("Expression \"{:s}\"".format(param) + \
                            " matches multiple entries in the index file!")
        else: # count == 0
            missing.append(param)

    # Missing messages?
    if len(missing) > 0:
        print("[!] Could not find: {:s}".format(", ".join(missing)))
        if stopifnot: raise Exception("Some parameters not found in index file! Check config.")

    # Return ranges to be downloaded
    return res


# -------------------------------------------------------------------
# -------------------------------------------------------------------
class read_config():

    def __init__(self, file):
        """read_config(file)

        Reading the required configuration from the config file.

        Parameters
        ----------
        file : str
            name/path of the configuration file

        Returns
        -------
        No return, initializes a new class of type mos_config with a set
        of arguments used to download/process the GFS forecasts.
        """

        self.params   = {} # Default value, no parameters to load
        self.file     = [] # Used to store the config file names
        self.read(file)

    def get(self, key):
        """get(key)

        Returns attribute \"key\" from the object. If not found,
        a ValueError will be raised.

        Parameter
        ---------
        key : str
            name of the attribute

        Returns
        -------
        Returns the value of the attribute from the object if existing,
        else a ValuerError will be raised.
        """
        if not hasattr(self, key):
            raise ValueError("read_config has no attribute \"{:s}\"".format(key))
        return getattr(self, key)

    def __repr__(self):

        res = "HRRR Configuration:\n"
        res += "   Config read from (seq):    {:s}\n".format(", ".join(self.file))
        res += "   Number of parameters:      {:d}\n".format(len(self.params))
        res += "   Forecast steps:            {:s}\n".format(", ".join([str(x) for x in self.steps]))
        res += "   Forecast runhours:         {:s}\n".format(", ".join([str(x) for x in self.runhours]))
        res += "   Where to store grib files: {:s}\n".format(self.gribdir)
        res += "\n   Parameters:\n"
        for p in self.params:
            res += "   - {:10s} {:s}\n".format(p, self.params[p])
        return(res)

    def read(self, file):

        if not isinstance(file, str):
            raise ValueError("input \"file\" has to be a string (read_param_config method)")
        from os.path import isfile
        if not isfile(file):
            raise ValueError("the file file=\"{:s}\" does not exist".format(file))
                
        # Read parameter configuration.
        import sys
        import configparser
        CNF = configparser.RawConfigParser()
        CNF.read(file)

        # Append file
        self.file.append(file)
        self._read_domain(CNF)
        self._read_params(CNF)
        self._read_steps(CNF)
        self._read_runhours(CNF)
        self._read_gribdir(CNF)
        self._read_url(CNF)
        self._read_curl(CNF)

        # If one of the required items is missing: stop
        for key in ["file", "url", "params", "steps", "runhours", "gribdir"]:
            if not hasattr(self, key):
                raise Exception("have not found proper \"{:s}\" definition in config file.".format(key))

    def _read_domain(self, CNF):
        # Domain
        try:
            self.domain = CNF.get("main", "domain")
        except Exception as e:
            raise Exception(e)

    def _read_url(self, CNF):
        # GFS archive server
        try:
            self.url = CNF.get("main", "url")
        except Exception as e:
            raise Exception(e)

    def _read_gribdir(self, CNF):
        try:
            self.gribdir = CNF.get("main", "gribdir")
        except:
            return

    def _read_params(self, CNF):

        # If not yet set: create a new dictionary
        self.params = {} # Initialize empty dictionary
        if not CNF.has_section("params"):
            raise Exception("Config file has no 'params' section.")

        # Adding ':cur' if needed (the default, current value)
        import sys
        from re import compile
        pattern = compile(r".*?:.*?:.*?")
        for key,val in CNF.items("params"):
            if pattern.match(val):
                self.params[key] = "{:s}".format(val)

    def _read_steps(self, CNF):

        try:
            steps = CNF.get("main", "steps")
        except:
            return

        # Trying to decode the user value
        from re import match, findall
        from numpy import unique, arange
        if match("^[0-9]+$", steps):
            self.steps = [int(steps)]
        elif match("^[0-9,\s]+$", steps):
            self.steps = [int(x.strip()) for x in steps.split(",")] 
            self.steps = list(unique(self.steps))
        elif match("^[0-9]+/to/[0-9]+/by/[0-9]+$", steps):
            tmp = findall("([0-9]+)/to/([0-9]+)/by/([0-9]+)$", steps)[0]
            self.steps = list(arange(int(tmp[0]), int(tmp[1])+1, int(tmp[2]), dtype = int))
        else:
            raise Exception("misspecified option \"steps\" in [main] config section.")
            
    def _read_runhours(self, CNF):

        try:
            runhours = CNF.get("main", "runhours")
        except:
            return

        # Trying to decode the user value
        from re import match, findall
        from numpy import unique, arange
        if match("^[0-9]+$", runhours):
            self.runhours = [int(runhours)]
        elif match("^[0-9,\s]+$", runhours):
            self.runhours = [int(x.strip()) for x in runhours.split(",")] 
            self.runhours = list(unique(self.runhours))
        elif match("^[0-9]+/to/[0-9]+/by/[0-9]+$", runhours):
            tmp = findall("([0-9]+)/to/([0-9]+)/by/([0-9]+)$", runhours)[0]
            self.runhours = list(arange(int(tmp[0]), int(tmp[1])+1, int(tmp[2]), dtype = int))
        else:
            raise Exception("misspecified option \"runhours\" in [main] config section.")
 
    def _read_curl(self, CNF):

        # Defaults
        self.curl_timeout   = 10
        self.curl_retries   = 0
        self.curl_sleeptime = 5
        # Set custom values (if specified in the config file)
        for key in ["timeout", "retries", "sleeptime"]:
            try:
                setattr(self, "curl_{:s}".format(key), CNF.getint("curl", key))
            except:
                continue


# -------------------------------------------------------------------
# -------------------------------------------------------------------
def download_range(config, grib, local, curlrange):
    """download_range(config, grib, local, curlrange)

    Actually downloading the data.

    Parameters
    ----------
    config : read_config object
        As returned by 'read_config()'
    grib : str
        URL of the grib file (source).
    local : str
        Name/path of the file on the local disc.
    curlrange : list
        Defines the byte ranges to be downloaded; as returned
        by 'get_required_bytes()'

    Return
    ------
    Returns boolean True on success, else False.
    """

    print("- Downloading data for {:s}".format(local))
    from os import makedirs
    from os.path import isdir, dirname
    
    if not isdir(dirname(local)):
        try:
            makedirs(dirname(local))
        except Exception as e:
            raise Exception(e)

    import pycurl
    from datetime import datetime as dt

    # Openftp logfile if set
    #if config.curl_logfile:
    #    curllog = open(config.curl_logfile, "a")
    #else:
    #    curllog = None
    curllog = open("_curl.log", "a")

    # Start downloading the file
    timer = dt.now()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, grib)

    retries_left = config.curl_retries
    success = False
    # Download with retries if set
    while retries_left >= 0:
       print("Retries left: {:d}".format(retries_left))
       try:
          fp = open("{:s}.tmp".format(local), "wb")
          c.setopt(pycurl.WRITEDATA, fp)
          c.setopt(c.NOPROGRESS, 0)
          if config.curl_timeout:
             print("Curl timeout is {:d}".format(config.curl_timeout))
             c.setopt(pycurl.CONNECTTIMEOUT, config.curl_timeout)

          c.setopt(pycurl.FOLLOWLOCATION, 0)
          print("Downloading -> {:s}.tmp".format(local))

          for i in range(0, len(curlrange)):
             c.setopt(c.RANGE, curlrange[i])
             c.perform()

          if curllog:
             now    = dt.now()
             nowstr = now.strftime("%Y-%m-%d %H:%M:%S")
             curllog.write(" {:s}; {:6d}; {:16s}; {:s}\n".format(nowstr,
                int((now-timer).seconds), "success", local))
          fp.close()
          success = True
          break
       except Exception as e:
          print("Problems with download")
          print(e)
          retries_left -= 1
          if curllog:
             now    = dt.now()
             nowstr = now.strftime("%Y-%m-%d %H:%M:%S")
             curllog.write(" {:s}; {:6d}; {:16s}; {:s}\n".format( nowstr,
                int((now - timer).seconds),"ftp-error-{:d}".format(e[0]), local))
          if config.curl_sleeptime:
             log.info("Sleeping {:.0f} seconds and retry download".format(config.curl_sleeptime))
             time.sleep(config.curl_sleeptime)

    # Rename the file (after success)
    if success:
        from shutil import move
        move("{:s}.tmp".format(file.get("local")), file.get("local"))

    return success



