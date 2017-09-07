========
dotfiles
========

The *dotfiles* adapter handles git repositories (or local folders) that contain information about packages to install as well as configuration files for those packages. Once checked out, *freckles* will install the listed packages and link the configuration files to the appropriate location inside a users home directory.


Usage
-----

.. code-block:: console

   freckles dotfiles [OPTIONS] --freckle <freckle_url_or_path>

At least one path or url to a freckle needs to be provided (multiple paths can be supplied by simply providing multiple ``--freckle`` options, e.g. ``--freckle gh:makkus/dotfiles-test-simple --freckle gh:makkus/dotfiles-test-simple-2``)

Options
^^^^^^^

``--freckle``
    the path or url that points to a 'dotfiles' freckle

``--no-stow``
    flag to disable the 'stow' step of this adapter completely, no symbolic links will be created

``--no-install``
    flag to disable the 'install' step of this adapter completely, no packages will be installed

``--pkg-mgr``
    the (default) pkg_mgr to use, defaults to 'auto' (which is the system default package manager, e.g. apt, yum, homebrew). Also supported: 'conda', 'nix' and most of the package managers that have an Ansible module (those might need to be installed in an extra step as not all of them are natively supported by *freckles* yet

Metadata
--------

Metadata that can be provided within the *freckle* itself, either via the ``.freckle`` file in the root of the *freckle* directory, or via marker files.

vars
^^^^

``packages``
    a list of packages to install

``pkg_mgr``
    the (default) pkg_mgr to use, defaults to 'auto' (which is the system default package manager, e.g. apt, yum, homebrew). Also supported: 'conda', 'nix' and most of the package managers that have an Ansible module (those might need to be installed in an extra step as not all of them are natively supported by *freckles* yet

``no_install``
    flag to disable installing a package (mostly useful for the folder-based package specification)

``no_stow``
    flag to disable the 'stowing' (symlinking) of files in a application config folder


*freckle* folder structure
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

     <freckle-root>
           ├── <pkg_name_1>
           │      └── <pkg1_config>
           │              └── [.package.freckle] (optional)
           │              └── [.no_install.freckle] (optional)
           │              └── [.no_stow.freckle] (optional)
           │              └── <pkg1_config_file_2>
           │              └── <pkg1_config_file_2>
           ├── <pkg_name_2>
           │      └── <pkg2_config>
           │              └── [.package.freckle] (optional)
           │              └── [.no_install.freckle] (optional)
           │              └── [.no_stow.freckle] (optional)
           │              └── <pkg2_config_file_1>
           │

Additional files and markers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The *dotfiles* adpater supports two maker files, ``.no_install.freckle`` and ``.no_stow.freckle``, as well as an additional metadata file that allows for more fine grained configuration on a per-package-folder basis.

``.no_install.freckle``
    if an empty file named ``.no_install.freckle`` is found inside a package folder, this folder is not used when calculating package names based on sub-folder names.

``.no_stow.freckle``
    if an empty file named ``.no_stow.freckle`` is found inside a package folder, this folder will not be 'symbolically linked' to the users home directory

``.package.freckle``
    if a file named ``.package.freckle`` is found inside a package folder, the variables that are specified inside override (or augment) the ones found in the parent ``.freckle`` metadata file, but only for the package in question. For example, if such a file contains ``pkg_mgr: nix`` as content, the package in question will be installed using the ``nix`` package manager, while all other ones might be installed using the system package manager


Example ``.freckle`` files
^^^^^^^^^^^^^^^^^^^^^^^^^^

Simple packages list, using the 'default' package manager
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This is the simplest, and probably most common case. Just a list of package names.

.. code-block:: yaml

   dotfiles:
     packages:
       - emacs
       - htop
       - zile


Alternative (supported) package managers
++++++++++++++++++++++++++++++++++++++++

Currently *freckles* supports  *conda* and *nix* as alternative options to install packages. If any of those is specified, but not present on the system, it'll be installed before *freckles* attempts to install any packages.

TODO: more details about supported/unsupported package managers

.. code-block:: yaml

   dotfiles:
     pkg_mgr: conda
     packages:
       - mongodb
       - nano


Alternative (unsupported) package managers
++++++++++++++++++++++++++++++++++++++++++

Although at the moment *freckles* only supports a few selected package managers, Ansible has modules for quite a few more. It's possible to use those by using the name of the ansible module as value for the ``pkg_mgr`` key.

.. code-block:: yaml

   dotfiles:
     pkg_mgr: pip
     packages:
       - cookiecutter
       - thefuck

Multiple package managers
+++++++++++++++++++++++++

By providing multiple `*dotfiles*` keys, and assigning different ``pkg_mgr`` values, it is possible to specify lists of packages that use different package managers.

.. code-block:: yaml

   - dotfiles:
      pkg_mgr: auto
      packages:
        - gawk
        - pypy
        - pypy-dev

  - dotfiles:
      pkg_mgr: nix
      packages:
        - di
        - emacs
        - fasd-unstable
        - git-crypt

Package list for multiple platforms:
++++++++++++++++++++++++++++++++++++

Sometimes it's handy to be able to use the same list of packages on different platforms. Unfortunately the package names are not always guaranteed to be the same in such a situation. Here's how to specify a multi-platform list of packages:

.. code-block:: yaml

  dotfiles:
    packages:
      - emacs
      - fortune-package:
          pkgs:
            apt:
              - fortunes
              - fortunes-off
              - fortunes-mario
            yum: fortune-mod
            homebrew:
              - fortune
            other: omit

If ``pkg_mgr`` is set to auto, the default package manager of the system you currently use will  be used to install the package.

TODO: link to package list format
TODO: link to advanced options

Prevent installing any packages based on child-folder names for a freckle
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

By default the *dotfiles* adapter uses the names of first-level child folders as package names for packages to be installed. Sometimes when this behaviour is not wanted it can be disabled either in the ``.freckle`` file:

.. code-block:: yaml

   dotfiles:
     no_install: true

Or via an (empty) marker file called ``.no_install.freckle`` in the root of the *freckle* folder.
  

Examples
--------

Below are some more exmaples with a detailed explanations to illustrate how to use the *dotfiles* adapter.

Simple folder structure, no extra metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This describes the simplest possible use-case: you want to store configuration in a git repository, but only use one platform (Debian, Redhat, Mac OS X, ...) or can assume that the package name for the applications you want to configure is the same for the system package managers of all the platforms you intend to use.

In it's most simple form, a `*dotfiles*` freckle is a folder that contains subfolders named after the package of the application to install, and the configuration files for that application inside the subfolder:

.. code-block:: console

     <freckle-root>
           ├── <pkg_name_1>n
           │      └── <pkg1_config>
           ├── <pkg_name_2>
           │      └── <pkg2_config>
           │

The configuration files are layed out as they would be if they were located in the users home directory. So, e.g. *fish* (a shell) needs a configuration file ``$HOME/.config/fish/config.fish``. In this case the path to the configuration file would be: ``<freckle-root>/fish/.config/fish/config.fish``. *freckles* will ensure (with the help of stow_) that ``config.fish`` will be symbolically linked from it's actual location to where *fish* expects it to be.

I've prepared an example repository containing two applications (``fish``, and ``zile``, an emacs-like text editor -- I tried to find applications that are not super-likely to conflict with what people are already using, to make it easier to try this out) here: https://github.com/makkus/dotfiles-test-simple). The package names for those two should be the same on all major package managers, so in theory you can try this out on any of the platforms that are supported by *freckles*:

.. code-block:: console

   curl https://freckles.io | bash -s -- freckles dotfiles -f gh:makkus/dotfiles-test-simple

   # or, if you already have freckles installed and in your $PATH, just:

   freckles dotfiles -f gh:makkus/dotfiles-test-simple

(from now on I'll assume you already have *freckles* installed, and either logged out and logged in again, or did a ``source ~/.profile`` to make sure it's in your path)

This will:

- bootstrap freckles (if not already there)
- install ``git``, if necessary, in order to:
- check out the url https://github.com/makkus/dotfiles-test-simple.git to ``$HOME/freckles/dotfiles-test-simple``
- install those two applications according to the names of the top-level sub-folders: ``fish`` & ``zile``
- `stow` the contents of the two top-level sub-folders into the home directory


Mixing and matching two ``dotfile`` freckles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now, lets assume you are an avid user of both ``fish`` and ``zile``, so you install them everywhere you do work on (your laptop, every Vagrant_ dev box, every Docker_ container (while you are still developing your Dockerfile) remote ssh servers, etc...).

*freckles* lets you do that fairly easily in all of those cases, doing what we did above. Now, in some cases you want some additional applications which are unnecessary in others. For example, say, on systems where you have a graphical frontend you want to have the the terminator_ X terminal available.

You don't want to put that into the same `*dotfiles*` *freckle* as the other two packages, since that would install it every time, even on system where that doesn't make sense (like a container). So, one way to do this would be to create a 2nd, separate `*dotfiles*` *freckle* which contains the ``terminator`` config directory. I've done this here: https://github.com/makkus/dotfiles-test-simple-2

Now, on systems where we want to have both sets of dotfiles (and applications installed), we can do this:

.. code-block:: console

    freckles dotfiles -f gh:makkus/dotfiles-test-simple -f gh:makkus/dotfiles-test-simple-2

One little thing we have to adjust so ``stow`` is happy with us *stowing* from two different source directories: we have to create (empty) marker files with the filename ``.stow`` in the root of each *freckle*.


Mixing and matching two sets of dotfiles, using only one *freckle*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can achive the same outcome as in the above example by creating subfolders in the same *freckle*. In order to let *freckles* know which folders are a *freckle*, we need to mark those with an empty file named ``.freckle``. Thus, the folder structure will look like this:

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

Note that the root folder is itself not a *freckle* anymore. It just contains two of them.

To use both (sub-) *freckles*, just issue:

.. code-block:: console

   freckles dotfiles -f gh:makkus/dotfiles-test-simple-combined

If you only want the *minimal* sub-folder, you can do either:

.. code-block:: console

    freckles --include minimal dotfiles -f gh:makkus/dotfiles-test-simple-combined
    # or
    freckles --exclude gui-pkgs dotfiles -f gh:makkus/dotfiles-test-simple-combined

Both ``--include`` and ``--exclude`` options check whether the (full) path to the *freckle* ends with the provided string. If it does, the directive is applied to the *freckle*.


Include metadata to install additional packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the above examples we didn't add any *freckles* specific metadata to the *freckle* folders itself (except for the ``.freckle`` marker files in the last example).

This is useful for cases where we don't own the repository ourself, but we want to use the code therein and know it has a compatible structure. In most cases we'll have access to the repository though, which means we can augment the code or data itself with some metadata that helps *freckles* decide how to deal with it.

Internally, *freckles* uses frkl_ to parse this metadata. *frkl* tries to provide a way to keep configuration data as simple and readable as possible, as long as that is feasable. If the complexity of what the metadata is supposed to express increases, the *frkl* metadata schema can sorta 'expand' accordingly. *'elastic configuration'*, I think of it as. Anyway, for those examples I'll keep the configuration simple, if you want to learn more about *frkl* and what you can do if you need to do something out of the ordinary, check here_ (TODO: link)

*freckles* expects additional metadata in two places:

- the *.freckle* marker file in the root of a *freckle*
- any file inside a freckle that starts with a ``.`` and ends with ``.freckle``

If you want to provide additional metadata either way, the content of such a file needs to be `valid yaml`(TODO: link). Within *freckles* those two types are treated differently, and the second sort is used for more special cases, and might look different -- and have a different format -- for each implementation of a *freckles* profile.

For now, let's only worry about the first type. Here's the most simple example of such a file:

.. code-block:: yaml

   dotfiles:
     - packages:
         - gawk
         - pandoc
         - htop

This describes some additional packages we want to install. None of those uses configuration files (or maybe we are just not interested in keeping the configuration of those, no matter). Let's edit one of the ``.freckle`` marker files from the above example and include the above lines, then run:

.. code-block:: console

   freckles -f ~/freckles/dotfiles-test-simple-combined dotfiles

This time we want to use the *freckle* directly, locally, without checking out from git. We didn't commit our changes (the edits to the ``.freckle`` file), so if we ran the same command as before we'd see an error message. If all goes ok, ``freckles`` output should tell you it has installed those additional 3 applications (if they weren't already installed).

Metadata to include the package names of an application on different platforms/package managers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Part I: in ``.freckle``
.......................

Now it gets interesting. So far, we assumed all the systems you are using *freckles* on are more or less the same, and if you need to install the package it'll always have the same name. Unfortunately that is not the world we live in. Say, we really need the ``fortunes`` package, to have nice motd's. On Debian based platforms that package is called *'fortunes'*, and it is split up, or, rather, has some extra fortunes ('offensive', and 'mario', whatever that is). RedHat likes to call this *'fortune-mod'*, and in *homebrew* the name is *'fortune'*, without the trailing 's'.

Here's what we do:

.. code-block:: yaml

   dotfiles:
     - packages:
        - gawk
        - pandoc
        - htop
        - fortune-package:
            pkgs:
              apt:
                - fortunes
                - fortunes-off
                - fortunes-mario
              yum: fortune-mod
              homebrew:
                - fortune
              other: omit

In this case, the initial name (``fortune-package``) is only descriptive, it can be anything. Then, instead of a string like in the other package-names, we provide a dictionary, with the package name details for each package manager.

A few more things to notice:

- the matching of which package-name is selected is implemented quite fine-grained. This example only lists package names per package manager. You could also add platform names, or even distribution versions as keys here. I might provide some examples for this later on, for now you can check out the source code to get an idea: TODO: link
- the ``other: omit`` key/value is optional. It tells *freckles* to not bother if none of the package managers is available or specified. The ``other`` key could also contain a different string, which would be then viewed as the package name for any system where no match was found in the other options.
- the value for the pkg_mgr key can be either a string or a list, use whatever you like best, if you only have one package

Part II: in a ``.package.freckle`` file
.......................................

Now, what to do if you need to specify a package name per platform, but the application you are interested in has some config files you want to have managed, and *freckles* wants to install the package according to the root-level sub-folder name?

That's when the 2nd way of augmenting a *freckle* with metadata comes in: we use a file that starts with a ``.``, and ends with ``.freckle``. In the case of the `*dotfiles*` profile, this file needs to be called ``.package.freckle``, and it needs to sit in the application folder (e.g. ``<freckle_path>/fish/.package.freckle``).

If *freckles* executes the `*dotfiles*` folder, and finds any suchly named files, it'll overlay the key/values it finds in it ontop of the metadata it is working with.

So, say, we'd like to install *fortune* via the folder-method (which we don't, since there are no config files for it -- as far as I know), we'd have a ``.package.freckle`` file like this in ``<freckle_path>/fortune-package/.package.freckle`` (again, the ``fortune-package`` part is not important here):

.. code-block:: console

    pkgs:
      apt:
        - fortunes
        - fortunes-off
        - fortunes-mario
      yum:
        - fortune-mod
      homebrew:
        - fortune

Preventing some folders to be *stowed*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some cases you don't want *freckle* root-level child folders to be *stowed* (e.g. their location is hard-coded in some scripts, or whatever, you know it when you see it...).

This is easily done by setting the ``no_stow`` variable to 'true'. You can do this either in the ``.package.freckle`` file:

.. code-block:: console

   no_stow: true

or, by creating an (empty) file in the sub-folder you don't want *stowed*. Here's how my ``keysnail`` (a firefox browser extension) sub-folder config looks like:

.. code-block:: console

   x-applications
   ├── keysnail
       ├── .keysnail.js
       ├── .no_install.freckle
       ├── .no_stow_freckle
       └── plugins
           ├── builtin-commands-ext.ks.js
           ├── caret-hint.ks.js
           ├── _color-theme-solarized.ks.js
           ...
           ...

Preventing some folder to be *installed*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Similarly to the case above, sometimes you don't want to have a package with a sub-folder name installed. This works like ``no_stow``, but you set ``no_install`` instead (check out the *keysnail* folder example above).

Or, for completeness sake, the ``.package.freckle`` file:

.. code-block:: console

   no_install: true

More examples
^^^^^^^^^^^^^

Coming later...


.. _frkl: https://github.com/makkus/frkl
.. _stow: https://www.gnu.org/software/stow
.. _Vagrant: https://www.vagrantup.com/
.. _Docker: http://docker.com/
.. _terminator: http://gnometerminator.blogspot.com/p/introduction.html
