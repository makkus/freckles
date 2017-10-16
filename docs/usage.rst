#####
Usage
#####

The *freckles* project currently provides three command-line applications: ``freckelize``, ``frecklecute`` and ``freckles``. All of them share most of the underlying code, but they differ slightly in what they can do:

- ``freckelize`` helps retrieving a set of data or code, and preparing the host environment to handle it meaningfully
- ``frecklecute`` can execute a list of tasks (ansible modules and/or roles) defined in a yaml-formatted text file, to get the local machine into a certain state
- ``freckles`` binds the above two applications together, and lets you script their execution(s)

``freckelize`` is designed to require little to no configuration to achive its goal, ``frecklecute`` is more flexible, but needs a tad more effort in preparing the list of tasks:

.. toctree::
   :maxdepth: 5

   freckelize_command
   frecklecute_command
   freckles_command

``freckles`` consists of a few different commands, which all use the same underlying codebase and configuration format.

Notes
*****

Abbreviations
=============

``freckles`` applications mostly operate on urls. To make those urls more memorable, and also shorter, a few abbreviation schemes are supported (see below).

.. warning::
    This abbreviation scheme and/or the used format might change, don't depend on it for anything remotely approaching 'production'. I strongly recommend using 'full' urls for anything more than playing around.

- *github repo*: ``gh:<github_user>/<repo_name>``
- *github repo file*: ``gh:<github_user>/<repo_name>/path/to/file``
- *bitbucket_repo*: ``bb:<bitbucket_user>/<repo_name>``
- *bitbucket_repo_file*: ``bb:<bitbucket_user/<repo_name>/path/to/file``

