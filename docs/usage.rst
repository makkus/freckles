=================
Commands overview
=================

``freckles`` consists of a few different commands, which all use the same underlying codebase and configuration format.

A short side note: ``freckles`` applications mostly operate on urls. To make those urls more memorable, and also shorter, a few (optional -- you can still just provide the full url) abbreviation schemes are supported.

- *github repo*: ``gh:<github_user>/<repo_name>``
- *github repo file*: ``gh:<github_user>/<repo_name>/path/to/file``
- *bitbucket_repo*: ``bb:<bitbucket_user>/<repo_name>``
- *bitbucket_repo_file*: ``bb:<bitbucket_user/<repo_name>/path/to/file``


Following is a list of (currently) available commands:

freckles
========

- freckles usage page
- (currently) supported freckle profiles
- examples

``freckles`` is an application that downloads a remote code or data repository (I reckon it's a bit silly to call such a repository a `freckle`, right? too bad...) that is structured according to one or some conventions. After download, ``freckles`` will execute pre-defined tasks appropriate for the type of `freckle` in question.

For example, if the `freckle` is a python project, ``freckles`` will create a virtualenv named like the repository (after, if necessary, downloading everything that is needed to create virtualenvs in the first place), download and install all dependencies it can find in any potential ``requirement_*.txt`` files, and then execute ``python setup.py develop``, both inside the created virtualenv.

In fact, this is the recommended way to get started if one wants to contribute to the ``freckles`` project itself:

.. code-block:: console

   $ freckles gh:makkus/freckles

This will prepare a virtualenv in which development of the ``freckles`` project can be done.

Or, the `freckle` is a folder containing subfolders which in turn contain `dotfiles` (that's what configuration files are called in Unix-land). ``freckles`` will download this repo, install potentially configured applications that relate to the configuration files, and symbolically link those configuration files to the appropriate places.

Here is how I initialize a newly installed machine (Linux, Mac, VM, container, doesn't matter) using my dotfiles from https://github.com/makkus/dotfiles (using curl to bootstrap ``freckles`` itself as documented in the bootstrap page XXX):

.. code-block:: console

   $ curl https://frkl.io | bash -s -- freckles gh:makkus/dotfiles

This one command will automatically download my dotfiles repository onto the machine, then read all the ``.dotfiles.freckle`` metadata files contained within to find out which applications should be installed, and finally symbolically link (using an application called stow_ XXX) all the configuration files into their appropriate places in my home directory.

Checkout the above link for a list of currently supported profiles.

frecklecute
===========

    - frecklecute usage page
    - (currently) officially supported *frecklecutables*
    - examples

Where ``freckles`` automatically applies pre-configured tasks according to a profile, ``frecklecute`` is more flexible. It takes a ``yaml``-formatted text file (while we're assigning silly names, let's call those ``frecklecutables``, shall we?) as input, and executes the list of tasks contained in them.

That doesn't sound like much, for sure. Just a script of some sort script, using yaml. There are a few differences to 'normal' shell scripts though, and those might or might not make sense, depending on what needs to be done.

Most of those differences stem from the fact that ``freckles`` is built as a layer on top of ansible_, and uses the rich ecosystem of ansible modules and roles. Ansible is a powerful and rich configuration management system, and if you haven't heard from it, look it up, it is pretty impressive piece of code, in my opinion. Ansibles main purpose is to help setup and maintain compute infrastructure. You write some configuration that describes the setup of your environment, and ansible will make sure that environment is setup that way. More details about configuration management: XXX other page


One great thing about ansible (same is true for other configuration management systems) is that it has a very rich ecosystem of modules(XXX), which can be viewed as mini-applications that take a defined set of configuration, and do one item of work (delete a file, make sure a file contains a certain line, install an application). The neat thing is that those modules can be assembled into bigger pieces of work, which again can take a defined set of configuration. In ansible terms this can either be playbooks, or roles. It is difficult to explain how this differs from the building blocks of a shell scripts (shell commands) without having used both a configuration management system and shell scripts.

One such difference is that ``frecklecutables`` are (for the most part) idempotent. That means, if you run the same command a second time, you can be sure nothing changed on the machine you ran it on, and if it ran successfully the first time, it'll run successfully a second time. A shell script might run successfully one time, but might error out a second time, say, when it tries to create a folder it already created in an earlier run.


Anyway. Long story short, in some situations its good to use configuration management, sometimes its overkill, because of the overhead those systems introduce. This is the reason that configuration management is mainly used for managing infrastructure that crosses a certain threshold of, lets say... importance. Developer laptops or VMs don't often do that, except of course if the developer in question recognizes the importance of configuration management, and has the time and/or expertise to set it up.

So, now. While ansible itself is already quite user-friendly (for a configuration management system anyway), it takes a non-trivial amount of work to execute what is called in ansible terms a `playbook` (a list of tasks, or script if you will). For starters, ansible itself (and its dependencies) has to be installed. Then an inventory of hosts to manage has to be created (even if it is only used locally), some `ansible roles` (XXX) or other dependencies might have to be downloaded, and put in the right places. Finally you have to write the playbook itself. True, most of those things only need to be done once, and for the rest you can prepare templates. But in case you don't wanna, and you still want to take advantage of all the awesome ansible modules and roles out there, ``frecklecute`` is for you.

Say, you want to install

EXAMPLE XXX



.. _ansible: https://ansible.com
