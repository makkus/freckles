=======================
*freckelize your life!*
=======================

... or at least your laptop...


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


*freckles* is configuration management for your working environment (workstation, remote server, virtual machine, container), removing or hiding some more advanced features configuration management frameworks usually offer, for the sake of simplicity and a quick turnaround.

For now, *freckles* provides two (command-line) interfaces, which tackle slightly different scenarios and workflows: *freckles* itself, and *frecklecute*:

*freckles*
    a bit of an experiment, configuration management with a slight twist. Instead of describing your infrastructure, you describe the shape of your software or data, then *freckles* tries to figure out how to map that onto whatever (physical or virtual) hardware you are working on.

*frecklecute*
    basically a wrapper around ansible_, making it easier to get started writing and executing task lists ('playbooks') locally


Really quick-start
------------------

(... or a quick reminder how to bootstrap ``freckles``, if that's why you're here)

.. code-block:: console

   curl https://freckles.io | bash -s -- freckles --help

or, the same using ``curl``, and executing ``frecklecute`` (you can mix and match, of course):

.. code-block:: console

   wget -O - https://freckles.io | bash -s -- frecklecute --help

This bootstraps *freckles* or *frecklecute* (using inaugurate_, read more about the bootstrap process itself `here <https://github.com/makkus/inaugurate#how-does-this-work-what-does-it-do>`_), and displays its help message (instead of actually doing something useful). All files are installed under ``$HOME/.local/inaugurate/``, which can be deleted without affecting anything else.

This command also adds a line to your ``$HOME/.profile`` file in order to add *freckles* to your path (once you re-login, or do a ``source $HOME/.profile``). Set an environment var ``NO_ADD_PATH=true`` if you want to prevent that behaviour.

Features & use-cases
--------------------

* one-line setup of a new working environment (including freckles itself)
* minimal requirements: only ``curl`` or ``wget``
* supports Linux & MacOS X (and maybe the Ubuntu subsystem on Windows 10, not tested)
* uses the same configuration for your Linux and MacOS workstation as well as Vagrant machines, containers, etc.
* support for systems where you don't have root/sudo access via the conda_ package manager (or nix_, with some limitations)
* extendable via *profiles*
* declarative scripting, sorta
* 'self-loading' containers
* supports for all ansible `modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_ and `roles <https://galaxy.ansible.com/>`_

Examples
--------

using: *freckles*
^^^^^^^^^^^^^^^^^

Probably best to show what *freckles* is, and what it can do using examples. Do not try those below examples at home, as they'll install loads of packages you most likely don't need. I'll show you how I use *freckles* and *frecklecute* to install a new machine, after a) I buy a new Thinkpad or b) I did something silly that requires a re-install. Or, more often c) want to use all or parts of my dotfiles on a VM or container, to have a decent editor and shell while working in them.

Chapter #1, where we checkout our dotfiles and setup our development machine
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: console

   $ curl https://freckles.io | bash -s -- freckles dotfiles -f gh:makkus/dotfiles

This is what happens:

- bootstraps *freckles* itself, then straight away executes it
- expands the ``gh:makkus/freckles`` url to https://github.com/makkus/dotfiles (it's optional to have a short url, but I grew to like those)
- checks out the repository to ``$HOME/freckles/dotfiles`` (this is configurable of course)
- reads all the metadata  it can find in that repository, describing mostly which packages to install
- loads the instructions for the ``dotfiles`` profile, which:
- installs all the packages listed in the metadata (same metadata can be used to describe the setup on several flavors of Linux as well as on Mac OS X, you only have to provide the correct package names per package manager)
- symbolically links all the configuration files it finds in the repository into their appropriate place in my home directory (using an application called `stow` -- which *freckles* also installs if not present already)

I've organized my *dotfiles* into subfolders (to be able to exclude applications I don't need for certain scenarios -- e.g. X-applications in a VM), but that is more complicated than necessary. You can certainly just have a flatter folder-structure, with on subfolder per application.

Most of the above steps can be switched off, if necessary.

Chapter #2, where we setup a Python development project
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

Now, after setting up my machine with my applications and configuration files, I really need to start working on *freckles* again, because, as you can probably see, there's a lot to do still. Thus:

.. code-block:: console

   $ freckles python-dev -f gh:makkus/freckles

Here's what happens:

- freckles is already installed, so I can call it directly now (had to login again, or execute ``source $HOME/.profile`` to pick up the path *freckles* is installed in)
- as before, expands the url, from ``gh:makkkus/freckles`` to https://github.com/makkus/freckles
- checks out the repository to $HOME/freckles/freckles
- reads (optional)  metadata in the folder
- loads the instructions for the ``python_dev`` profile, which:
- installs the packages that are necessary (virtualenv and pycrypto dependencies, mostly, in this case)
- creates a virtualenv
- installs all the requirements it can find (in requirement*.txt files in the root folder of the repo) into the new virtualenv
- executes ``python setup.py develop`` within that same virtualenv

By default, virtualenvs are put under ``$HOME/.local/virtualenvs`` and are names after the foldername, with an appended ``-dev``. Thus, ``freckles-dev`` in our exmple. If I want to work on *freckles* I can activate the python virtualenv I just created via:

.. code-block:: console

   source $HOME/.local/virtualenvs/freckles-dev/bin/activate

using: *frecklecute*
^^^^^^^^^^^^^^^^^^^^

Chapter #3, where we run an ansible task as well as an external ansible role
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

So -- having setup all the data, associated applications, source code and working environment(s) I need -- there are a few other housekeeping tasks to do. For example, in the configuration of the minimal emacs-like editor ``zile`` I sometimes use I specified that it should put all backups into ``~/.backups/zile``. That directory doesn't exist yet, and if it doesn't exists, ``zile`` doesn't create it automatically, and consequently does not store any backups of the files I'm working on. So I have to make sure that folder gets created.

Also, and I'm making this up now, I might want to have docker installed on that new machine. The install procedure of docker is a bit more complicated so it can't be easily added to my dotfiles configuration. Luckily though, there are tons of ansible roles on https://galaxy.ansible.com that can do the job for us. The only thing we need to check is that the role supports the platform we are running.

For those more specialized tasks *freckles* is not a really good fit (although we could probably create a profile for this), it's easier to use *frecklecute*. *frecklecute* operates on (yaml) text files (I call them *frecklecutables* -- I know, I know...) that contain a list of ansible tasks and/or roles to execute, along with configuration for those tasks and roles. Here's a quick *frecklecutable* to create the folder I need, and install docker using the a role i found on ansible galaxy: https://galaxy.ansible.com/mongrelion/docker/ (I picked that one randomly, so not sure how well it actually works)

.. code-block:: yaml

   tasks:
     - file:
        path: ~/.backups/zile
        state: directory
     - mongrelion.docker:
        meta:
         become: yes

I'll not explain how this works in detail here (instead, check out: XXX), but basically *frecklecute* allows you to use all the ansible modules that are listed here: http://docs.ansible.com/ansible/latest/list_of_all_modules.html as well as all roles on `ansible galaxy <https://galaxy.ansible.com>`_.

Right. Let's save the above yaml block into a file called ``housekeeping.yml``. And let *frecklecute* do its thing:

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
-----------------

- this whole thing is still very much work in progress, so things might break, or they might break your machine. Use at your own risk.
- error messages are very raw, testing is, apart from a few bits and pieces, non-existent
- almost no tests yet, this is basically just a working prototype
- by it's nature, *freckles* changes your system and configuration. Whatever you do is your own responsibity, don't just copy and paste commands you don't understand.
- everything ``git`` related is done using the `ansible git module <http://docs.ansible.com/ansible/latest/git_module.html>`_, which 'shadows' a git repository with the latest remote version, if the local version has commited changes that aren't pushed yet. Nothing is lost, but it's an inconvenience when that happens.

License
-------

* Free software: GNU General Public License v3


Credits
-------

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


