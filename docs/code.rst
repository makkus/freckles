####
Code
####

*freckles* is written in *Python*, licensed under the GPLv3.

Main project
************

All the *freckle* source code can be found in it's github repo: https://github.com/makkus/freckles

Dependencies
============

During the development of *freckles*, a few code parts were refactored into their own projects, as they could potentially be used for other purposes in the future:

frkl
----

A library to enable 'elastic' configuration.

- homepage: https://github.com/makkus/frkl

nsbl
----

A library that generates Ansible environments, inventories, roles and playbooks out of more minimal, 'elastic' configuration.

- homepage: https://github.com/makkus/nsbl

inaugurate
----------

A project to enable 'drive-by' bootstrapping.

- homepage https://github.com/makkus/inaugurate


freckles ansible roles
======================

Internally, *freckles* uses several Ansible roles for bootstrap and other purposes. The full list of all the roles that ship with *freckles* can be viewed `here <https://github.com/makkus/freckles/tree/master/freckles/external/default_role_repo>`_. Here's a list of the most important ones:

makkus.box-basics
-----------------

Used for basic bootstrapping tasks.

- homepage: https://github.com/makkus/box-basics

makkus.freckles
---------------

The central role for the ``freckles`` command-line application. Used to download a *freckle*, then parse its metadata and forward that metadata to the appropriate adapter(s).

- homepage: https://github.com/makkus/freckles_ansible

makkus.install-freckles
-----------------------

An Ansible role that can install *freckles* (although that functionality is not used by ``freckles`` itself, obviously), and, more importantly, update it.

- homepage: https://github.com/makkus/install-freckles

makkus.freckles-config
----------------------

A role to do some *freckles* related configuration work, e.g. enable external adapter/role repositories and then check out said adapter/role repositories.

- homepage: https://github.com/makkus/freckles-config

makkus.install-pkg-mgrs
-----------------------

Role that ensures required package managers are installed on the host system.

- homepage: https://github.com/makkus/install-pkg-mgrs

makkus.install-packages
-----------------------

A (convenience) role that ensures a list of packages is installed on the host system, using the specified package manager for each package.

- homepage: https://github.com/makkus/install-packages

makkus.install-conda
--------------------

A role to install the conda_ package manager.

- homepage: https://github.com/makkus/install-conda

makkus.install-nix
------------------

A role to install the nix_ package manager

- homepage: https://github.com/makkus/install-nix


makkus.install-vagrant
----------------------

A role to install Vagrant_, which in the context of *freckles* is considered also a package manager, as it can install Vagrant plugins.

- homepage: https://github.com/makkus/install-vagrant

makkus.dotfiles
---------------

The role used by the *freckles* :doc:`dotfiles </adapters/dotfiles>` adapter.

- homepage: https://github.com/makkus/dotfiles_ansible

makkus.python-dev
-----------------

The role used by the *freckles* :doc:`python-dev </adapters/python-dev>` adapter.

freckles ansible roles (external)
=================================

In addition to custom-written roles, *freckles* also makes use of some existing roles written by other people:

ansiblebit.oracle-java
----------------------

To install Oracle Java.

- homepage: https://github.com/ansiblebit/oracle-java

elliotweiser.osx-command-line-tools
-----------------------------------

To install the commandline-tools package on Mac OS X, also needed for homebrew.

- homepage: https://github.com/elliotweiser/ansible-osx-command-line-tools

geerlingguy.homebrew
--------------------

To install homebrew_ on Mac OS X.

- homepage: https://github.com/geerlingguy/ansible-role-homebrew




.. _conda: https://conda.io
.. _nix: https://nixos.org/nix/
.. _Vagrant: https://www.vagrantup.com
.. _homebrew: https://brew.sh/
