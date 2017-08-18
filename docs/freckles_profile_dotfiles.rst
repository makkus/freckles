========
dotfiles
========

The dotfiles profile handles git repositories (or local folders) that contain information about packages to install as well as configuration files for those packages. Once checked out, *freckles* will install the listed packages and link the configuration files to the appropriate location inside a users home directory.

Quick links
-----------

- full structure and metadata schema
- examples
- more examples

Examples
--------

Simple folder structure, no extra metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This describes the simplest possible use-case: you want to store configuration in a git repository, but only use one platform (Debian, Redhat, Mac OS X, ...) or can assume that the package name for the applications you want to configure is the same for the system package managers of all the platforms you intend to use.

In it's most simple form, a ``dotfiles`` freckle is a folder that contains subfolders named after the package name of the application to install, and the configuration files for that application inside the subfolder:

.. code-block:: console

     <freckle-root>
           ├── <pkg_name_1>n
           │      └── <pkg1_config>
           ├── <pkg_name_2>
           │      └── <pkg2_config>
           │

The configuration files are layed out as they would be if they would be located in the users home directory. So, e.g. *fish* (a shell) needs a configuration file ``$HOME/.config/fish/config.fish``. In this case the path to the configuration file would be: ``<freckle-root>/fish/.config/fish/config.fish``. *freckles* will ensure (with the help of stow_) that ``config.fish`` will be symbolically linked from it's actual location to where ``fish`` expects it to be.

I've prepared an example repository containing two applications (``fish``, and ``zile``, an emacs-like text editor -- I tried to find applications that are not super-likely to conflict with what people are already using, to make it easier to try this out) here: https://github.com/makkus/dotfiles-test-simple). The package names for those should be the same on all mayor package managers, so in theory you can try this out on any of the platforms that are supported by *freckles*:

.. code-block:: console

   curl https://freckles.io | bash -s -- freckles --profile dotfiles gh:makkus/dotfiles-test-simple

   # or, if you already have freckles installed and in your $PATH, just:

   freckles --profile dotfiles gh:makkus/dotfiles-test-simple

(from now on I'll assume you already have *freckles* installed, and either logged out or did a ``source ~/.profile`` to make sure it's in your path)

This will:

- bootstrap freckles (if necessary)
- install ``git``, if necessary, in order to:
- check out the url https://github.com/makkus/dotfiles-test-simple.git
- install the two applications according to the names of the top-level sub-folders: ``fish`` & ``zile``
- `stow` the contents of the two top-level sub-folders into the home directory

Mixing and matching two ``dotfile`` freckles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

THIS DOES NOT WORK CURRENTLY, DO TO A BUG IN ANSIBLE, PROBABLY. USE THE METHOD RIGHT BELOW.

Now, assuming you are an avid user of both ``fish`` and ``zile``, so you install them everywhere you do some work (your laptop, every Vagrant_ dev box, every Docker_ container (while you are still developing your Dockerfile) remote ssh servers, etc...). With *freckles* you can easily do that in all of those cases, doing what we did above. Now, in some cases you want some additional applications, which are unnecessary in others. For example, say, on systems where you have a graphical frontend you want to have the the terminator_ X terminal available.

You don't want to put that into the same ``dotfiles`` *freckle* as the other two packages, since that would install it every time, even on system where that doesn't make sense. So, one way to do this would be to create a 2nd ``dotfiles`` *freckle*, including the ``terminator`` config directory. I've done this here: https://github.com/makkus/dotfiles-test-simple-2

Now, on systems where we want to have both sets of dotfiles (and applications installed), we can do this:

.. code-block:: console

    freckles --profile dotfiles gh:makkus/dotfiles-test-simple gh:makkus/dotfiles-test-simple-2

One little thing we have to adjust so ``stow`` is happy with us *stowing* from two different source directories: we have to create (empty) marker files with the filename ``.stow`` in the root of each *freckle*.

Mixing and matching two sets of dotfiles, using only one *freckle*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can achive the same outcome as in the above example by creating subfolders in the same *freckle*. In order to let *freckle* know which folders are a *freckle*, we need to mark those with an empty file named ``.freckle``. Thus, the folder structure will look like this:

.. code-block:: console

    ├── gui-pkgs
    │   ├── .freckle
    │   ├── .stow
    │   └── terminator
    │       └── .config
    │           └── terminator
    │               └── config
    └── minimal
        ├── fish
        │   └── .config
        │       └── fish
        │           └── config.fish
        ├── .freckle
        ├── .stow
        └── zile
            └── .zile


Here I've create two sub-folders, called ``gui-pkgs`` and ``minimal`` to separate different usage scenarios. Notice also the two ``.stow`` marker files. We need those again, same as above. This example *freckle* can be found here: https://github.com/makkus/dotfiles-test-simple-combined

To use both (sub-)*freckles*, just issue:

.. code-block:: console

   freckles --profile dotfiles gh:makkus/dotfiles-test-simple-combined

If you only want the *minimal* sub-folder, you can do either:

.. code-block:: console

    freckles --profile dotfiles --include minimal gh:makkus/dotfiles-test-simple-combined
    # or
    freckles --profile dotfiles --exclude gui-pkgs gh:makkus/dotfiles-test-simple-combined

Both ``--include`` and ``--exclude`` options check whether the (full) path to the *freckle* ends with the provided string. If it does, the directive is applied.


Single *freckle*, including metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon....

.. _stow: https://www.gnu.org/software/stow
.. _Vagrant: https://www.vagrantup.com/
.. _Docker: http://docker.com/
.. _terminator: http://gnometerminator.blogspot.com/p/introduction.html
