#######################
*freckelize your life!*
#######################
... or maybe your laptop?


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

Introduction
************

*freckles* is configuration management for your working environment (workstation, remote server, virtual machine, container, ...), it removes (or hides) advanced features often offered by other configuration management frameworks, for the sake of simplicity and a quick turnaround.

*freckles* helps you bring your machine from a useless -- for your intent and purpose --state, into a useful one. With one line in a terminal.

Quick links
===========

- homepage: https://freckles.io
- documentation: https://docs.freckles.io
- code: https://github.com/makkus/freckles

For now, the *freckles* project provides two (command-line) interfaces, which deal with slightly different scenarios and workflows:

``freckles``
============

Configuration management for your desktop, with a slight twist. Instead of describing your infrastructure, you describe the shape of the code or data packages you work with, and *freckles* tries to figure out how to map that onto whatever (physical or virtual) hardware you are working on by using an appropriate *adapter* for that type of data.

One example would be pointing it to a repository of your (well, my, in this case) dotfiles:

.. code-block:: console

   freckles dotfiles -f gh:makkus/dotfiles

*freckles* will download the dotfiles repo, install all the applications that are referenced, then link the dotfiles themselves into the right place (for more details, check `the example below <Example #1, where we checkout our dotfiles and setup our development machine_>`_, or the ``dotfile`` adapter documentation `here <https://docs.freckles.io/en/latest/adapters/dotfiles.html>`_).

Or you can use *freckles* to get you started working on *freckles* itself by letting it download it's own source code and set up a development environment for it:

.. code-block:: console

   freckles python-dev -f gh:makkus/freckles

This will check out the *freckles* source code from `it's github repo <https://github.com/makkus/freckles>`_, install all the system dependencies *freckles* needs, creates a virtual environment called ``freckles-dev`` and installs *freckles* and its python dependencies into it (more details can be found `in the example below <Example #2, where we setup a Python development project_>`_ and the ``python-dev`` adapter documentation `here <https://docs.freckles.io/en/latest/adapters/python-dev.html>`_).

Or, maybe you are working on a webpage. If somebody writes an adapter for your usecase and the framework(s) you use, *freckles* could download your source files, setup a webserver and potential dependencies (nodejs? php? ruby?, ...) on your dev machine, then puts configuration in place so you can start working straight away.

``frecklecute``
===============

Basically a wrapper around Ansible_, making it easier to get started writing and executing task lists ('playbooks' in Ansible-speak) locally. It allows you to execute short (yaml) scriptlets ('*frecklecutables*'). As *freckles* and *frecklecute* are built on top of *Ansible*, `all Ansible modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_, as well as `all roles on Ansible galaxy <https://galaxy.ansible.com>`_ can be used as building blocks for such a *frecklecutable*.

*frecklecute* comes with a few default *frecklecutables*, for example one (called `'ansible-task' <https://github.com/makkus/freckles/blob/master/freckles/external/frecklecutables/ansible-task>`_) that lets you execute any arbitrary Ansible module or role directly. This is what it looks like to ensure a folder exists, using *frecklecute* (including '`inaugurating <inaugurate_>`_'/bootstrapping *frecklecute* itself):

.. code-block:: console

   curl https://freckles.io | bash -s -- frecklecute -pw false ansible-task --task-name file --vars '{"path": "~/cool_folder", "state": "directory"}'

This has to be, by the way, the most bloated and roundabout way to create a folder in the history of creating folders. We've come a long way from ``mkdir`` :-) . Although, of course, that particular example doesn't make any sense, I hope it is plain to see how use- and powerful a scripting tool like this, with access to all Ansible modules and roles, can be. Let's use another example and install Docker (using the `mongrelion.docker <https://galaxy.ansible.com/mongrelion/docker/>`_ role from Ansible galaxy -- I'll asume *frecklecute*/*freckles* is already installed this time):

.. code-block:: console

   frecklecute ansible-task --become --task-name mongrelion.docker

This will install docker with everything that is required on your local machine (check the `source code of the role <https://github.com/mongrelion/ansible-role-docker>`_ to see what exactly it is doing, and how, and which target environments it supports).

In addition to using the pre-existing *frecklecutables*, it's easy to `write your own <https://docs.freckles.io/en/latest/writing_frecklecutables.html>`_. Using the two tasks above, we could write one like the following (note how it's possible to make a cli option for the ``path`` var), and store it in a file called ``example.yml``:

.. code-block:: yaml

    args:
      path:
        help: the folder path
        default: ~/cool_folder
    tasks:
      - file:
         state: directory
      - mongrelion.docker:
          meta:
            become: yes

Then run it like so:

.. code-block:: console

    frecklecute example.yml --path ~/another_cool_folder


Really quick start
******************

(... or a quick reminder how to bootstrap *freckles*, if that's why you're here)

Most examples above assume you have *freckles* already installed. If that's not the case, *freckles* can be bootstrapped using 'inaugurate_' (yes, yes, I know, downloading and executing scripts from random websites is often considered a bad idea -- so before you continue you might want to read `this <https://github.com/makkus/inaugurate#how-does-this-work-what-does-it-do>`_, `this <https://github.com/makkus/inaugurate#is-this-secure>`_, and `this <https://docs.freckles.io/en/latest/bootstrap.html>`_ ). To install *freckles* and run it straight away to display it's help, issue:

.. code-block:: console

   curl https://freckles.io | bash -s -- freckles --help

or, using ``wget`` instead of ``curl``, and executing ``frecklecute`` instead of ``freckles`` (you can mix and match, of course):

.. code-block:: console

   wget -O - https://freckles.io | bash -s -- frecklecute --help

This bootstraps ('inaugurates') *freckles* or *frecklecute* and displays its help message (instead of actually doing something useful). All files are installed under ``$HOME/.local/inaugurate/``, which can be deleted without affecting anything else.

This command also adds a line to your ``$HOME/.profile`` file in order to add *freckles* to your path (once you re-login, or do a ``source $HOME/.profile``). Set an environment var ``NO_ADD_PATH=true`` if you want to prevent that behaviour.

More detailed information on this and other ways to install *freckles* can be found `here <https://docs.freckles.io/en/latest/bootstrap.html>`_.

Features
********

* one-line setup of a new working environment (including *freckles* itself)
* minimal initial requirements: only ``curl`` or ``wget``
* supports Linux & MacOS X (and maybe the Ubuntu subsystem on Windows 10, not tested yet)
* can use the same configuration for your Linux and MacOS workstation as well as Vagrant machines, containers, etc.
* support for systems where you don't have root/sudo access via the conda_ package manager (or nix_, with some limitations)
* extensible via *adapters*
* declarative, idempotent scripting, sorta
* allows the use of all ansible `modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_ and `roles <https://galaxy.ansible.com/>`_

Some actual/potential usecases
******************************

* easily replicate configuration across machines
* use configuration to document the setup of your working environment
* quickly re-install your workstation after a potential security incident (or a border crossing?), or after you did something to your filesystem you now realize you shouldn't have done
* 'self-loading' containers
* share the same project setup with your team-mates
* provide an (easy-to-read, understand and re-use) *frecklecutable* or *freckle adapter* alongside a blog post you wrote about some useful workstation setup (e.g. 'how to secure your workstation', or 'how to setup a python dev environment', ...)
* create base environments for tutorials etc.
* quick and easy config management for small networks, which can grow into a 'proper' Ansible-managed infrastructure if necessary
* quickly create install/update scripts for your scripts/applications where it's not worthwhile to create 'traditional' packages
* minimal, initial bootstrap/config management for your Ansible/Chef/saltstack controllers -- I mean, you need to set those up too, right?
* anything else where you need to make sure your environment needs to be in a certain state but for some reason or other you don't want to use a 'full-blown' configuration management system


Examples
********

Probably best to show what *freckles* is, and what it can do using examples. Do not try those at home, as they'll install loads of packages you most likely don't need.

I'll show you how I use *freckles* and *frecklecute* to install a new machine, after a) I buy a new Thinkpad or b) unfortunately way more often, did something silly that requires a re-install. Or, even more often still, c) want to use parts of my personal configuration on a VM or container or remote server, to have a decent editor and shell and such available while working in/on them. Then I'll show how to use *freckles* on the *freckles* source code itself. And finally I'll quickly outline how to use *frecklecute* to do some other, more specialized, housekeeping tasks.


using: *freckles*
=================


Example #1, where we checkout our dotfiles and setup our development machine
----------------------------------------------------------------------------

On a newly installed machine, I run:

.. code-block:: console

   $ curl https://freckles.io | bash -s -- freckles dotfiles -f gh:makkus/dotfiles

This is what happens:

- bootstraps *freckles* itself, then straight away executes it
- expands the ``gh:makkus/freckles`` url to https://github.com/makkus/dotfiles (it's optional to have a short url, but I grew to like those)
- checks out the repository to ``$HOME/freckles/dotfiles`` (this is configurable of course)
- reads all the metadata  it can find in that repository, describing mostly which packages to install
- loads the instructions for the ``dotfiles`` adapter, which:
- installs all the packages listed in the metadata (same metadata can be used to describe the setup on several flavors of Linux as well as on Mac OS X, you only have to provide the correct package names per package manager)
- symbolically links all the configuration files it finds in the repository into their appropriate place in my home directory (using an application called stow_ -- which *freckles* also installs if not present already)

In case you had a look at `my dotfiles repo <https://github.com/makkus/dotfiles>`_: I've organized my configuration into subfolders (to be able to exclude applications I don't need for certain scenarios -- e.g. X-applications on a remote server), but that is more complicated than necessary. You can certainly just have a flat folder-structure, with one subfolder per application.

Most of the above steps can be switched off, if necessary. More information about the adapter used in this example: `dotfiles <https://docs.freckles.io/en/latest/adapters/dotfiles.html>`_.

Example #2, where we setup a Python development project
-------------------------------------------------------

Now, after setting up my machine with my applications and configuration files, I really need to start working on *freckles* again, because, as you can probably see, there's a lot to do still. Thus:

.. code-block:: console

   $ freckles python-dev -f gh:makkus/freckles

Here's what happens:

- freckles is already installed, so I can call it directly now (had to login again, or execute ``source $HOME/.profile`` to pick up the path *freckles* is installed in)
- as before, expands the url, from ``gh:makkkus/freckles`` to https://github.com/makkus/freckles
- checks out the repository to ``$HOME/freckles/freckles``
- reads (optional)  metadata in the folder
- loads the instructions for the ``python_dev`` adapter, which:
- installs the packages that are necessary (virtualenv and pycrypto dependencies, mostly, in this case)
- creates a virtualenv
- installs all the requirements it can find (in requirement*.txt files in the root folder of the repo) into the new virtualenv
- executes ``pip install -e .`` in the project folder, within that same virtualenv

By default, virtualenvs are put under ``$HOME/.local/virtualenvs`` and are named after the project folder, with an appended ``-dev``. Thus, ``freckles-dev``, in our exmple. If I want to work on *freckles* I can activate the python virtualenv *freckles* just created via:

.. code-block:: console

   source $HOME/.local/virtualenvs/freckles-dev/bin/activate

More information about the ``python-doc`` adapter: `python-doc <https://docs.freckles.io/en/latest/adapters/python-dev.html>`_.

using: *frecklecute*
====================

Example #3, where we run an ansible task as well as an external ansible role
----------------------------------------------------------------------------

So -- having setup all the data, associated applications, source code and working environment(s) I need -- there are a few other housekeeping tasks to do. For example, in the configuration of the minimal emacs-like editor ``zile`` I sometimes use, I specified ``zile`` should put all backups into ``~/.backups/zile``. That directory doesn't exist yet, and if it doesn't exist, ``zile`` doesn't create it automatically, and consequently does not store any backups of the files I'm working on. So I have to make sure that folder gets created.

Also I want to have Docker installed on that new machine. The install procedure of Docker is a bit more complicated than an simple ``apt-get install docker``, and because of that I can't easily add it to my dotfiles configuration. Luckily though, there are tons of ansible roles on https://galaxy.ansible.com that can do the job of installing Docker for me. The only thing I need to check is that the role supports the platform I am running.

For those more specialized tasks *freckles* is not a really good fit (although we could probably create an adapter for this, or expand the existing ``dotfiles`` one), so it's easier to use *frecklecute*. *frecklecute* operates on (yaml) text files (I call them *frecklecutables*) that contain a list of Ansible tasks and/or roles to execute, along with configuration for those tasks and roles. Here's a short *frecklecutable* to create the folder I need, and install *docker* using a role I found on Ansible galaxy: https://galaxy.ansible.com/mongrelion/docker/

.. code-block:: yaml

   tasks:
     - file:
        path: ~/.backups/zile
        state: directory
     - mongrelion.docker:
        meta:
         become: yes

I'll not explain how all this works in detail here (instead, check out `this <https://docs.freckles.io/en/latest/frecklecute_command.html>`_), but basically *frecklecute* allows you to create a list of tasks in a yaml file, using the names of `any of the existing ansible modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_, and/or the name of any of the `roles on ansible galaxy <https://galaxy.ansible.com>`_, which then gets read and executed consecutively.

Right. Let's save the above yaml block into a file called ``housekeeping.yml``. And let *frecklecute* do it's thing:

.. code-block:: console

   frecklecute housekeeping.yml

You'll see something like:

.. code-block:: console

    Downloading external roles...
      - downloading role 'docker', owned by mongrelion
      - downloading role from https://github.com/mongrelion/ansible-role-docker/archive/master.tar.gz
      - extracting mongrelion.docker to /home/vagrant/.cache/ansible-roles/mongrelion.docker
      - mongrelion.docker (master) was installed successfully

    * starting tasks (on 'localhost')...
     * starting custom tasks:
         * file... ok (changed)
       => ok (changed)
     * applying role 'mongrelion.docker'......
       -  => ok (no change)
       - ensure docker dependencies are installed =>
           - [u'apt-transport-https', u'ca-certificates'] => ok (no change)
       -  => ok (no change)
       - Download docker setup script for desired version => ok (no change)
       - Execute docker setup script =>
       ...
       ...
       ...

Neat, eh?

(Current) caveats
*****************

- this whole thing is still very much work in progress, so things might break, or they might break your machine. Use at your own risk.
- error messages are very raw, testing is, apart from a few bits and pieces, non-existent
- sometimes, cancelling it's execution can result in some runaway tasks (e.g. a kicked-off 'apt' process isn't killed and will run until it is finished by itself) -- this doesn't happen often, and it's usually of no consequence. But important to know I guess.
- by it's nature, *freckles* changes your system and configuration. Whatever you do is your own responsibity, don't just copy and paste commands you don't understand.
- everything ``git`` related is done using the `ansible git module <http://docs.ansible.com/ansible/latest/git_module.html>`_, which 'shadows' a git repository with the latest remote version, if the local version has commited changes that aren't pushed yet. Nothing is lost, but it's an inconvenience when that happens.
- mostly developed on Debian & Ubuntu, so RedHat-based platforms and Mac OS X might not work as well just yet (although I spent a shitload of time to support Mac OS X, so it shouldn't be far off)
- as *freckles* and it's adapters use conventions to minimize the need for configuration, it is fairly opinionated on how to do things, necessarily. You might, for example, not like the way ``dotfiles`` are 'stowed' (preferring maybe using an external git work-tree, or whatnot), or how the ``python-dev`` adapter handles python code. That being said, it is certainly possible to just write another adapter, or add different options to existing ones.


License
*******

* Free software: GNU General Public License v3


Credits
*******

For *freckles* (and the libraries that developed because of it, nsbl_ and frkl_) I am relying on quite a few free libraries, frameworks, ansible-roles and more. Here's a list, I hope I did not forget anything. Let me know if I did.

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
