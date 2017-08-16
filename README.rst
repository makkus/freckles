============
**freckles**
============

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

*freckles* is configuration management for your working environment (workstation, remote server, virtual machine, container), with a slight twist. Instead of describing your infrastructure, you describe the requirements of your software or data. *freckles* tries to figure out how to map that onto whatever you are working on.

Really quick-start
------------------

(... or a quick reminder how to bootstrap *freckles*, if that's why you're here)

.. code-block:: console

   curl https://freckles.io | bash -s -- freckles --help

or

.. code-block:: console

   wget -O - https://freckles.io | bash -s -- freckles --help

This bootstraps *freckles*, and displays its help message. All files are installed under ``$HOME/.local/inaugurate/``, which can be deleted without affecting anything else. This command also adds a line to your ``$HOME/.profile`` or ``$HOME/.bashrc`` file in order to add *freckles* to your path (once you re-login, or do a ``source $HOME/.profile``).

Features
--------

* one-line setup of a new environment, including freckles bootstrap
* minimal requirements: only ``curl`` or ``wget``
* supports Linux & MacOS X (and probably the Ubuntu subsystem on Windows 10)
* uses the same configuration for your Linux and MacOS workstation as well as Vagrant machines, containers, etc.
* support for systems where you don't have root/sudo access via the conda_ package manager (or nix_, with some limitations)
* declarative scripting
* direct support for all ansible_ modules and roles

Examples
--------

Best to show what *freckles* is, and what it can do using examples, right? Do not try those below examples at home, as they'll install loads of packages you most likely don't need.

Example #1, manage your dotfiles and the setup of your development machine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   $ curl https://freckles.io | bash -s -- freckles gh:makkus/dotfiles

This is what I use to setup a new machine, after a) I buy a new Thinkpad or b) I did something silly that requires a re-install. Or, more often c) want to use parts of my dotfiles on a VM or container, to have a decent editor and shell when working in them. Either way, what this does is:

- bootstraps *freckles* itself, then straight away executes it
- expands the ``gh:makkus/freckles`` url to https://github.com/makkus/dotfiles (it's optional to have a short url, but I grew to like those)
- checks out the repository to ``$HOME/freckles/dotfiles`` (this is configurable of course)
- reads all the metadata  it can find in that repository, describing mostly which packages to install
- installs all the packages listed in the metadata (same metadata can be used to describe the setup on several flavors of Linux as well as on Mac OS X, you only have to provide the correct package names per package manager)
- metadata also says that this repository is of type  ``dotfiles``, so *freckles* goes ahead and symbolically links all the configuration files it finds in the repository into their appropriate place in my home directory (using an application called `stow` -- which *freckles* also installs if not present already)

I've organized my *dotfiles* into subfolders (to be able to exclude applications I don't need for certain scenarios -- e.g. X-applications in a VM), but that is more complicated than necessary. You can certainly just have a flatter folder-structure, with on subfolder per application.

Here's how the (common part) of the metadata looks like: XXX link. And here is how the ``dotfiles`` profile works: XXX link

Example #2, setting up the environment for a Python development project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now, after setting up my machine with my applications and configuration files, I really need to start working on *freckles* again, which, I guess I should tell you, is not all that finished or stable just yet. Which is why I have to start working on *freckles* again, see. Thus:

.. code-block:: console

   $ freckles gh:makkus/freckles

Here's what happens:

- freckles is already installed, so I can call it directly now (had to login again, or execute ``source $HOME/.profile`` to pick up the path *freckles* is installed in)
- as before, expands the url, from ``gh:makkkus/freckles`` to https://github.com/makkus/freckles
- checks out the repository to $HOME/freckles/freckles
- reads the metadata, installs the packages that are necessary (virtualenv and pycrypto dependencies, mostly, in this case)
- also figures out this is a python dev project, so it:

  - creates a virtualenv
  - installs all the requirements it can find (in requirement*.txt files in the root folder of the repo) into the new virtualenv
  - executes ``python setup.py develop`` within that same virtualenv


* Free software: GNU General Public License v3
* Documentation: https://freckles.readthedocs.io.

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
.. _`geerlingguy/ansible-role-homebrew`: https://github.com/geerlingguy/ansible-role-homebrew
.. _`elliotweiser.osx-command-line-tools`: https://github.com/elliotweiser/ansible-osx-command-line-tools
.. _mac_pkg: https://github.com/spencergibb/battleschool/blob/7f75c41077d73cceb19ea46a3185cb2419d7c3e9/share/library/mac_pkg
.. _battleschool: https://github.com/spencergibb/battleschool
