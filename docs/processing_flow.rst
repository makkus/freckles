===============================
Processing flow inside freckles
===============================

Flow
----

Config strings
--------------
This is how freckles processes a config file:

The commandline takes in a list of strings, which are processed in the order they appear in.

Each string can either be a local path, a remote url, or a json-dictionary. Local files are read and converted from yaml to a python dictionary. Remote urls are used to download the files they point to, then read as yaml and converted to a python dict. Json dictionaries are converted directly into a python dict.

So, each string basically represents a dictionary, with two potential keys: ``vars`` and ``runs``. If neither one of those keys is present, it is assumed that the file contains vars and the (dictionary) value of the string is put into a new dictionary as the value of a ``vars``-key. (NOT IMPLEMENTED YET, XXX)

``vars`` are processed first, and are overlayed over each other sequentially. Once a ``run`` is encountered, the current ``var`` is snapshotted und stored for the next config item, so it can be overlayed with that. A copy of that snapshot is used when processing the ``run`` variable.

The value for a ``runs`` key is always a list of items. Each of those items is a dict with 3 potential keys: ``vars``, ``name``, ``frecks``. The ``vars`` key works similar to the lower-level ``vars`` we encountered earlier. Key/Value-pairs in there will be overlayed over the snapshot that was made earlier and are valid for every one of the ``frecks`` (which are sort of sub-run-tiems).

The ``name`` keys value is used to hold a short description of what a particular run is supposed to do, and is used at execution time, to display progress details, as well as a sort of config-file documentation string.

The main item of interest is referenced by the ``frecks`` key. The value of this key again is a list. Each item can be either a string or a dictionary. In case of a string, it specifies the name of the freck to run, and it is assumed the freck does not have any (extra) custom configuration, or we want to use the frecks' default configuration.

In case of a dictionary, the dictionary needs to be of length 1. The key is the name of the freck (same as if it would have been a string), and the value again is a dictionary with 2 potential valid keys: ``vars``, ``name``. ``name`` again is just a short description of what this item does.

``vars`` is either a list of dictionaries or a dictionary. In case of a list, it is assumed that this freck should be run multiple times, each time with the dictionary-item overlayed over the current snapshot-vars (that in turn could have been overlayed with ``run``-specific vars). In case of a dictionary the freck will only be run once, with the dictionary itself overlayed.
