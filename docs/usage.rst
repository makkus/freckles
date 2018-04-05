#####
Usage
#####

The *freckles* project currently provides three command-line applications: ``freckelize``, ``frecklecute`` and ``freckles``. All of them share most of the underlying code, but they differ slightly in what they can do:

- ``freckelize`` helps retrieving a set of data or code, and preparing the host environment to handle it meaningfully
- ``frecklecute`` can execute a list of tasks (ansible modules and/or roles) defined in a yaml-formatted text file, to get the local machine into a certain state
- ``freckles`` binds the above two applications together, and lets you script their execution(s)

In addition, the project also provides a tool to help developing *adapters*, *frecklecutables* and *ansible roles*: ``freckfreckfreck``

For more details, check out any or all of those:

.. toctree::
   :maxdepth: 5

   freckelize_command
   frecklecute_command
   freckles_command
   freckfreckfreck_command


Common options and conventions
******************************

As All three cli tools (`freckles`, `freckelize`, `frecklecute`) are mostly using the same underlying code, and do basically the same thing but providing slightly different interfaces. This is why they share a few cli options and usage conventions, which can be used in all of them:


cli options/arguments
=====================

`--user-repo`: add one or more context repositories
---------------------------------------------------

I'm not sure yet whether 'context repository' is a good name, but what I mean is a repository that contains *Ansible roles*, *frecklecutables* and/or *freckelize adapters*. The idea is that a user creates one or several of those, and collects trusted *roles*, *frecklecutables* and *adapters* in them. If they want to do some work that is not supported by the plugins and roles that come with *freckles*, they can tell any of the applications to download one or several of those repositories just before the run starts, and use the code that's in them. That way the user can be sure they only run 'trusted' code (apart from *freckles* and it's dependencies of course), as well as there are no version changes in any of the plugins between the last time they were used and now.

`--ask-become-pass`: ask the user for a *sudo* password
-------------------------------------------------------

This is an area of *freckles* that still needs some polishing, and maybe some re-design. A lot of things one wants *freckles* to do require *sudo*/*root* permissions. Installing applications, creating files in system folders, etc. There are a lot of things that don't require those, mostly concerning things happening in the users home directory, e.g. creating Python virtualenvs, installing *conda* packages, checking out git repositories.

Then there is the environment *freckles* is run on. For example, if run within a *Vagrant* box, no *sudo* password is required because most of those are configure for passwordless sudo. Same for some remote servers. Or, if run under the root account, *freckles* likewise doesn't need to ask for a password.

Ideally, *freckles* or any of it's *cli*'s would only ask for a *sudo* password if necessary, because if you know you don't need to provide a password you can, for example, include the *freckles* command in a script without having to worry about it stopping mid-way through.

How this is done at the moment is that there is the `--ask-become-pass` flag, which can be set to either 'auto', 'true', or 'false'. At the moment 'auto' and 'true' behave mostly the same way, except when calling `frecklecute`. Because `frecklecute' can reasonably assume to know whether *sudo* permissions are required or not by parsing through the list of tasks and their metadata, if set to 'auto' it'll only ask for a password if it finds at least one tasks that has the 'become' flag set.

To not unnecessarily ask for a *sudo* password on systems where *passwordless sudo* is configured for the account running a *freckles* application, *freckles* tries to execute `sudo ls` before starting a run. If that succeeds, it won't ask for a password. If it does not, it'll. Only if `--ask-become-pass` is set to 'true' or 'auto' though.

`--no-run`: only create the Ansible environment, don't execute the playbook
---------------------------------------------------------------------------

This is mostly for debugging purposes, but it could potentially also be used to automatically create an Ansible playbook environment that can be copied to different systems and be executed there, without needing *freckles* installed (*Ansible* would still have to be installed of course).

The (last) created environment can be found in `$HOME/.local/share/freckles/runs/current`.


Abbreviations
=============

``freckles`` applications mostly operate on urls. To make those urls more memorable, and also shorter, a few abbreviation schemes are supported (see below).

.. warning::
    This abbreviation scheme and/or the used format might change, don't depend on it for anything remotely approaching 'production'. I strongly recommend using 'full' urls for anything more than playing around.

- *github repo*: ``gh:<github_user>/<repo_name>``
- *github repo file*: ``gh:<github_user>/<repo_name>/path/to/file``
- *bitbucket_repo*: ``bb:<bitbucket_user>/<repo_name>``
- *bitbucket_repo_file*: ``bb:<bitbucket_user/<repo_name>/path/to/file``
