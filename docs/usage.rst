#####
Usage
#####

The *freckles* project currently provides two command-line applications: ``freckles`` and ``frecklecute``. Both use mostly the same underlying code, but they differ slightly in what they can do:

- ``freckles`` helps retrieving a set of data or code, and preparing the host environment to handle it meaningfully
- ``frecklecute`` can execute a list of tasks (ansible modules and/or roles) defined in a yaml-formatted text file, to get the local machine into a certain state

The former is designed to require little to no configuration to achive its goal, the latter is more flexible, but needs a tad more effort in preparing the list of tasks:

.. toctree::
   :maxdepth: 5

   freckles_command
   frecklecute_command

``freckles`` consists of a few different commands, which all use the same underlying codebase and configuration format.

Notes
*****

Abbreviations
=============

``freckles`` applications mostly operate on urls. To make those urls more memorable, and also shorter, a few (optional -- you can still just provide the full url) abbreviation schemes are supported.

- *github repo*: ``gh:<github_user>/<repo_name>``
- *github repo file*: ``gh:<github_user>/<repo_name>/path/to/file``
- *bitbucket_repo*: ``bb:<bitbucket_user>/<repo_name>``
- *bitbucket_repo_file*: ``bb:<bitbucket_user/<repo_name>/path/to/file``



frecklecute
===========

    - frecklecute usage page
    - (currently) officially supported *frecklecutables*
    - examples
