.. image:: https://img.shields.io/pypi/v/freckles.svg
           :target: https://pypi.python.org/pypi/freckles

.. image:: https://img.shields.io/travis/makkus/freckles.svg
           :target: https://travis-ci.org/makkus/freckles

.. image:: https://readthedocs.org/projects/freckles/badge/?version=latest
           :target: https://docs.freckles.io/en/latest/?badge=latest
           :alt: Documentation Status

.. image:: https://pyup.io/repos/github/makkus/freckles/shield.svg
           :target: https://pyup.io/repos/github/makkus/freckles/
           :alt: Updates

.. image:: https://badges.gitter.im/freckles-io/Lobby.svg
           :alt: Join the chat at https://gitter.im/freckles-io/Lobby
           :target: https://gitter.im/freckles-io/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge


########
freckles
########


*freckles* is a collection of tools designed to manage your local working environment (workstation, remote server, virtual machine, container, ...). It supports you and your team in applying best practices -- similar to those used in the configuration management and DevOps space -- on all of your development (and other) projects. And hopefully saving you time while doing it.

Currently, *freckles* consists of two main applications:

`freckelize <https://docs.freckles.io/en/latest/freckelize_command.html>`_
   a tool to facilitate `data-centric environment management <https://freckles.io/blog/data-centric-environment-management>`_, which means it'll look at a project folder, process it's structure and metadata, then it'll setup a hospitable environment for that project on the host system, according to a set of pre-written recipes (which ideally follow best practices for the type of project in question)

`frecklecute <https://docs.freckles.io/en/latest/frecklecute_command.html>`_
   an interpreter for `declarative, idempotent command-line scripts <https://freckles.io/blog/writing-declarative-commandline-scripts>`_, which can make use of `all Ansible modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_ as well as `all roles on Ansible galaxy <https://galaxy.ansible.com>`_

*freckles* is written in Python, and uses Ansible_ to do the heavy (system- and state-management) lifting.


- `Quick links`_
- Examples_
- `Project goals`_
- `Project features`_
- `Install/bootstrap`_
- License_
- Credits_

Quick links
***********

- homepage: https://freckles.io
- documentation: https://docs.freckles.io
- code: https://github.com/makkus/freckles


Examples
********

``freckelize``
==============

*freckelize* supports the quick and easy creation of plug-ins for all sorts of project-types and -data. It comes with a a number of default ones, as well as examples to illustrate it's workings and capabilities. Here are a few of those:

Python project
--------------

The following command can setup a development environment around any Python project. This here sets up one for the *freckles* project itself. *freckles* is written in Python and uses a fairly standard project structure. This command will checkout the *freckles* source code, install Python (version 2) as well as a few required system dependencies (if not already installed), then create a `virtualenv <http://www.pythonforbeginners.com/basics/how-to-use-python-virtualenv>`_ for the project, and install all the Python project dependencies into it using ``pip``:

.. code-block:: console

    $ freckelize python-dev -f gh:makkus/freckles


- project repository used in this example: https://github.com/makkus/freckles (expanded from ``gh:makkus/freckles``)
- metadata used in this example: https://github.com/makkus/freckles/blob/master/.freckle
- ``python-dev`` adapter and (Ansible) role used:

   - adapter doc: https://docs.freckles.io/en/latest/adapters/python-dev.html
   - adapter source: https://github.com/freckles-io/adapters/tree/master/languages/python/python-dev
   - role source: https://github.com/freckles-io/freckles-io.python-dev


Wordpress
---------

Here we setup a new `Wordpress <https://wordpress.com>`_ instance, using a so called `blueprint <http://localhost:8000/freckelize_command.html#blueprints>`_, which is basically a prepared, generic (and in most cases empty) project template with some defaults set, that can optionally ask for user input for some of those defaults and change the project template accordingly.

The following will ask the user a few basic answers about the install. Then it'll install and configure a *MySQL* server, *PHP* and *PHP packages* necessary for *Wordpress*, as well as the *Nginx* web-server. If so specified by the user, it'll also request a "Let's encrpyt" https certificate for the domain running this *Wordpress* instance, and it'll setup a cronjob to renew that certificate before it expires.

You'll end up with a folder under ``/var/lib/freckles`` which contains everything relevant to your Wordpress install (both database and Wordpress-site files), which can be easily backed-up. And which can be used to quickly restore your instance on a different, newly installed machine (again, using *freckles*).

.. code-block:: console

    $ freckelize -r frkl:wordpress -f blueprint:wordpress -t /var/lib/freckles


- context repository used in this example: https://github.com/freckles-io/wordpress (expanded from: ``frkl:wordpress``)
- blueprint used: https://github.com/freckles-io/wordpress/tree/master/blueprints/wordpress
- ``wordpress`` adapter source: https://github.com/freckles-io/wordpress/tree/master/adapters/wordpress
- more info:

   - https://freckles.io/blog/example-wordpress
   - `screencast for this example <https://freckles.io/blog/example-wordpress/wordpress-install.ogv>`_
   - `run log for this example <https://pastebin.com/raw/EVrzyrMS>`_


dotfiles
--------

If you use a curated repository of dotfiles to manage your application configuration, the following command can setup your usual development environment on a newly provisioned machine (physical or virtual), without any manual interaction. It uses the structure of the dotfiles repository as well as potentially added metadata to determine which applications to install, and how to configure them (if applicable):

.. code-block:: console

    $ freckelize -f gh:makkus/dotfiles-test-simple


- dotfiles repository used in this example: https://github.com/makkus/dotfiles-test-simple
- metadata used in this example: https://github.com/makkus/dotfiles-test-simple/blob/master/.freckle
- ``dotfiles`` adapter and (Ansible) role used:

   - adapter doc: https://docs.freckles.io/en/latest/adapters/dotfiles.html
   - adapter source: https://github.com/freckles-io/adapters/tree/master/configuration-management/dotfiles
   - role source: https://github.com/freckles-io/freckles-io.dotfiles

- more info:

   - https://freckles.io/blog/managing-dotfiles
   - https://freckles.io/blog/how-to-manage-your-dotfiles-with-freckles
   - https://freckles.io/blog/how-to-manage-my-dotfiles-with-freckles


``frecklecute``
===============

TBD


Project goals
*************

*freckles* main goals are:

- encouraging users to record and version control important project metadata (e.g.: type of project, all project requirements: system- as well as framework/language specific)
- quick (re-)provisioning of project development environments (on both physical as well as virtual machines)
- replicated, identical development environments for all members of a development team (even if they use different platforms for development) -- including the installation and configuration of system-level dependencies
- provide best-practice blueprints for a wide range of project profiles, in order quickly get started with a well thought-out project structure, developed and agreed upon by the community as best practice
- allowing the re-use of all existing Ansible `modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_ and `roles <https://galaxy.ansible.com/>`_


Project features
****************

* one-line setup of a new working environment (including *freckles* itself)
* minimal initial requirements: only ``curl`` or ``wget``
* supports Linux & MacOS X (and maybe the Ubuntu subsystem on Windows 10, not tested yet)
* can use the same configuration for your Linux and MacOS workstation as well as Vagrant machines, containers, etc.
* support for systems where you don't have root/sudo access via the conda_ package manager (or nix_, with some limitations)
* extensible via *adapters*
* declarative, idempotent scripting


Install/bootstrap
*****************

The examples above assume you have *freckles* already installed. If that's not the case, *freckles* can be bootstrapped using the 'inaugurate_' bootstrap script (yes, yes, I know, downloading and executing scripts from random websites is often considered a bad idea -- so before you actually do, you might want to read `this <https://docs.freckles.io/en/latest/trust.html>`_, `this <https://github.com/makkus/inaugurate#how-does-this-work-what-does-it-do>`_, `this <https://github.com/makkus/inaugurate#is-this-secure>`_, and `this <https://docs.freckles.io/en/latest/bootstrap.html>`_ ). To install *freckles* and run ``freckelize`` straight away to display it's help, issue:

.. code-block:: console

   curl https://freckles.io | bash -s -- freckelize --help

or, using ``wget`` instead of ``curl``, and executing ``frecklecute`` instead of ``freckles`` (you can mix and match, of course, and also use the ``freckles`` command if that is what you need):

.. code-block:: console

   wget -O - https://freckles.io | bash -s -- frecklecute --help

This bootstraps ('inaugurates') ``freckelize``, ``frecklecute`` or ``freckles`` and displays its help message (instead of actually doing something useful). All files are installed under ``$HOME/.local/inaugurate/``, which can be deleted without affecting anything else.

This command also adds a line to your ``$HOME/.profile`` file in order to add *freckles* to your path (once you re-login, or do a ``source $HOME/.profile``). Set an environment var ``NO_ADD_PATH=true`` if you want to prevent that behaviour.

More detailed information on this and other ways to install *freckles* can be found `here <https://docs.freckles.io/en/latest/bootstrap.html>`_.


License
*******

* Free software: GNU General Public License v3


Credits
*******

For *freckles* (and the libraries that developed because of it, nsbl_ and frkl_) I am relying on quite a few free libraries, frameworks, ansible-roles and more. Here's a list for the main dependency libraries, and the first couple of Ansible roles that were used. There are a lot more now, so please forgive me if yours is not included below:

ansible_
    obviously the most important dependency, not much more to say apart from that without it *freckles* would not exist.

cookiecutter_
    also a very important piece for *freckles* to use, most of the templating that is not done directly with jinja2_ is done using *cookiecutter. Also, *freckles* (as well as nsbl_ and frkl_) use the `audreyr/cookiecutter-pypackage`_ template.

jinja2_
    a main dependency of *ansible* and *cookiecutter*, but also used on its own by *freckles*

click_
    the library that powers the commandline interfaces of *freckles*, *nsbl*, and *frkl*

nix_
    a super-cool package manager I use for most of my non-system packages. Also check out NixOS_ while you're at it. Ideally *freckles* wouldn't be necessary (or at least would look quite different) because everybody would be using Nix!

conda_
    similarly cool package manager, and the reason *freckles* can be bootstrapped and run without sudo permissions. This is a bigger deal than you probably realize.

homebrew_
    I'm not using MacOS X myself, but I'm told *homebrew* is cool, which is why I support it. And, of course because MacOS X doesn't have a native system package manager.

`geerlingguy.ansible-role-homebrew`_
    the role that installs homebrew on MacOS X, one of the few external ansible roles that *freckles* ships with

`elliotweiser.osx-command-line-tools`_
    the role that installs the XCode commandline tools on Mac OS X. Also ships with *freckles*, and is a dependency of *geerlingguy.ansible-role-homebrew*

ansible-nix_
    ansible module written by Adam Frey, which I did some more work on. Probably wouldn't have thought to support *nix* if I hadn't found it.

mac_pkg_
    ansible module written by Spencer Gibb for battleschool_, can install all sort of packages on a Mac. Can't tell you how glad I was not to have to write that.


.. _inaugurate: https://github.com/makkus/inaugurate
.. _nsbl: https://github.com/makkus/nsbl
.. _frkl: https://github.com/makkus/frkl
.. _ansible: https://ansible.com
.. _jinja2: http://jinja.pocoo.org
.. _click: http://click.pocoo.org
.. _cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _nix: https://nixos.org/nix/
.. _NixOS: https://nixos.org
.. _conda: https://conda.io
.. _ansible-nix: https://github.com/AdamFrey/nix-ansible
.. _homebrew: https://brew.sh/
.. _`geerlingguy.ansible-role-homebrew`: https://github.com/geerlingguy/ansible-role-homebrew
.. _`elliotweiser.osx-command-line-tools`: https://github.com/elliotweiser/ansible-osx-command-line-tools
.. _mac_pkg: https://github.com/spencergibb/battleschool/blob/7f75c41077d73cceb19ea46a3185cb2419d7c3e9/share/library/mac_pkg
.. _battleschool: https://github.com/spencergibb/battleschool
.. _stow: https://www.gnu.org/software/stow/
