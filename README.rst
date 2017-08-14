========
freckles
========


.. image:: https://img.shields.io/pypi/v/freckles.svg
        :target: https://pypi.python.org/pypi/freckles

.. image:: https://img.shields.io/travis/makkus/freckles.svg
        :target: https://travis-ci.org/makkus/freckles

.. image:: https://readthedocs.org/projects/freckles/badge/?version=latest
        :target: https://freckles.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/makkus/freckles/shield.svg
     :target: https://pyup.io/repos/github/makkus/freckles/
     :alt: Updates


*freckles* is configuration management for your development environment (physical box, virtual machine, container), with a slight twist. Instead of describing your infrastructure, you describe the requirements of your software or data. *freckles* tries to figure out how to map that onto whatever you are working on.

- Documentation: https://freckles.readthedocs.io
- Github: https://github.com/makkus/freckles
- pypi: https://pypi.python.org/pypi/freckles


Really quick-start
------------------

.. code-block:: console

   curl https://frkl.io | bash -s -- freckles --help

This bootstraps *freckles*, and displays its help message. All files are installed under ``$HOME/.local/inaugurate/``, which can be deleted without affecting anything else. This command also adds a line to your ``$HOME/.profile`` or ``$HOME/.bashrc`` file in order to add *freckles* to your path (once you re-login, or do a ``source $HOME/.profile``).

Features
--------

* one-line setup of a new environment, including freckles bootstrap
* minimal requirements: only ``curl`` or ``wget``
* supports Linux & MacOS X (and probably the Ubuntu subsystem on Windows 10)
* uses the same configuration for your Linux and MacOS workstation as well as Vagrant machines, containers, etc.
* support for systems where you don't have root/sudo access via the conda_ package manager (or nix_, with some limitations) -- or if you just link one or both of them
* direct support for all ansible_ modules and roles

Examples
--------

Best to show what *freckles* is, and what it can do using examples, right?

Example #1, manage your dotfiles and the setup of your development machine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   $ curl https://frkl.io | bash -s -- freckles gh:makkus/dotfiles

This is what I use to setup a new machine, after a) I buy a new Thinkpad or b) I did something silly that requires a re-install. Or, more often c) want to use parts of my dotfiles on a VM or container, to have a decent editor and shell when working in them. Either way, what this does is:

- bootstraps *freckles* itself, then straight away executes it
- expands the ``gh:makkus/freckles`` url to https://github.com/makkus/dotfiles (it's optional to have a short url, but I grew to like those)
- checks out the repository to ``$HOME/freckles/dotfiles`` (this is configurable of course)
- reads all the metadata  it can find in that repository, describing mostly which packages to install
- installs all the packages listed in the metadata (same metadata can be used to describe the setup on several flavors of Linux as well as on Mac OS X, you only have to provide the correct package names per package manager)
- metadata also says that this repository is of type  ``dotfiles``, so *freckles* goes ahead and symbolically links all the configuration files it finds in the repository into their appropriate place in my home directory (using an application called `stow` -- which *freckles* also installs if not present already)

I've organized My *dotfiles* into subfolders (to be able to exclude applications I don't need for certain scenarios -- e.g. X-applications in a VM), but that is more complicated than necessary. You can certainly just have a flatter folder-structure, with on subfolder per application.

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


Other
-----

If you are familiar with ansible_, puppet_, chef_, or saltstack_, you know about configuration management, and why it (mostly) is a good idea. If not: in short, configuration management gives you a way to describe a machine/server and the services and applications it runs. Either in code, or a configuration format like json or yaml. Then it takes that configuration and applies it to a machine, removing the need for you to setup the machine maunually, as well as guaranteeing that the machine is always setup the same way, even after a re-install.

Because of the overhead that come with configuration management systems, using them is usually restricted to situations where the infrastructure to be controlled is deemed to cross a certain threshold of... let's call it 'importance'. While for production services, or other business-relevant systems this threshold is often crossed even for single servers, this is not usually the case for the physical (or virtual) machines developers (or somesuch) use when going about whatever they go about. There are exceptions of course, but spending the time to learn about, and then setting up a system like that is not always worth it. *freckles* tries to change that equation by making it easier, and faster, to apply the principles of configuration management to local development environments. I do think there's a lot of developers time to be saved, to be used on actual development, rather than all the annoying stuff around it...

Blahblah. Yes, sorry. Example, to keep you interested:


Those two are the only so-called *profiles* I have implemented so far: ``dotfiles`` and ``python-dev``. *freckles* is written in a way to add more of those profiles fairly easily though, my reasoning being that its a good idea to have a set of 'commonly used', 'best-practices' profile of how code should be structured, and which metadata is necessary to describe certain 'expressions' of that code or data (e.g. a python project could need to be setup in a development environment, or installed from source for 'normal' use).

I haven't finished thinking about all potential pros and cons yet, but so far I think that metadata should sit with the code itself (with a few minor exceptions like for example where on the target machine it should be checked out). Once that is done, we can have systems do things automatically to get the target system in the state that is determined by the code itself, the profile used, and some aspects of the host machine (e.g. which OS is running on it, which package managers are available).

The nice thing about this is that this gives you all the advantages of an automated system to manage your working space, while still allowing flexibiliy in how to deal with certain types of code/data. For example, you don't like the ``stow`` way of symbolically linking dotfiles? Well, just create a profile that sets up your dotfiles using a detached git repostory (XXX link). As long as the repository contains the name of the profile in its metadata, all is good.

Right. There's more, but I realize this is already too much text for a project Readme. So instead of writing more text here, I'll write more text elsewhere:

 - frecklecute
 - freckles profiles
 -


* Free software: GNU General Public License v3
* Documentation: https://freckles.readthedocs.io.


Features
--------

* TODO

Credits
---------

mac_pkg: Spencer Gibb ( https://github.com/spencergibb/battleschool )

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage


.. _ansible: https://ansible.com
.. _puppet: https://puppet.com
.. _chef: https://www.chef.io/chef
.. _saltstack: https://saltstack.com
.. _nix: https://nixos.org/nix/
.. _conda: https://conda.io
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _ansible-nix: https://github.com/AdamFrey/nix-ansible
.. _homebrew: https://brew.sh/
