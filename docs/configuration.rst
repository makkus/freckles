=============
Configuration
=============

Runs and config overlays
------------------------

Freckles executes one or multiple runs per execution. Each run in turn executes one or multiple items (plugings for Freckles, called 'Frecks'). Each such Freck has its own configuration, although, depending on the circumstances, those configurations can be very similar to each other and only differ in one value.

In order to support a certain degree of flexibility, and also to make configuration short, easy and reusable, Freck configuration items are overlayed in the order they are provided. A Freck config can either be the path to a local yaml file, the url to a remote yaml file, or a json string.

Each configuration item contains a dictionary with one or both of those two keys: ``vars`` and ``runs``:

  vars:
      This contains key-value pairs that are used to configure all the Frecks that are specified after this vars declaration (except they are overwritten by a subsequent ``vars`` block).

      Example:
          vars:
            dotfiles:
              - /home/markus/dotfiles
            pkg_mgr: nix

  runs:
      A list of dictionaries, each describing a run. As mentioned above, each run can execute multiple Frecks, and different Frecks need different configuration keys. If no additional configuration is provided, Freckles will forward the current ```vars`` environment to each freck of a run`. If a run has a ``vars`` key of its own, this will be overlayed over the current 'global' ``vars`` environment, and then used to configure its child Frecks. Those ``run`` specific vars will not go into the global ``vars`` environment though, which means subsequent runs won't see them.

      Frecks are described in the value to the ``frecks`` key. The value is either a string (the freck type -- if no extra configuration is needed) a dictionary with the type of the Freck (e.g. ``install``, ``stow``, etc.) as (only) key, and another dictionary with one or both of those keys: ``name`` (a short descriptive name of what this Freck does) and ``vars`` (another overlay, this time over the run-specific ``vars`` environment).

      Example:
          runs:
            - name: bootstrap
              vars:
                 some: value
                 another: value
              frecks:
                 - install-nix
            - name: install & stow
              vars:
                 some: other value
                 dotfiles: /home/markus/dotfiles  # dotfiles is needed by both ``install`` and ``stow``
              frecks:
                 - install:
                   name: install stuff
                   vars:
                     pkg_mgr: nix
                 - stow  # does not need any other configuration than the dotfiles one


Dotfiles
--------

For two of the central modules in freckles (*install* and *stow*), a dotfile directory needs to be specified as input.

A dotfile directory is a folder that contains other folders, which in turn contain configuration files for certain applications ('*dotfiles*'). In Freckles, each dotfile directory has 3 components:


base_dir
  the base path to the local holder (optional, defaults to $HOME/dotfiles)

remote
  the url to a remote git repository (optional, not used if not specified)

paths
  a list of relative sub-paths, on top of *base_dir* (optional, defaults to an empty list)


In the core freckles modules, if no value at all is provided, this default is used:

::

    vars:
      dotfiles:
        - base_dir: ~/dotfiles
          paths: []
          remote: ""

For convenience, if a user wants to manage and check-out the dotfiles directory themselves (of if they have done so already), a single string indicating the path to the folder can be used instead of a dictionary:

::

    vars:
      dotfiles:
        - ~/dotfiles

In contrast, if the user is happy with the default local dotfiles location, and does want freckles to checkout the remote dotfiles repo there automatically, they can specify a remote url as the sole input string:

::

    vars:
      dotfiles:
        - https://github.com/makkus/dotfiles.git

This will be converted internally to:

::

    vars:
      dotfiles:
        - base_dir: ~/dotfiles
          paths: []
          remote: https://github.com/makkus/dotfiles.git

For when one dotfile repository contains several sub-folders to split up the dotfiles into discreet units that can be mixed and matched differently on different machines, it's possible to describe those units using the *paths* property:

::

    vars:
      dotfiles:
        - base_dir: ~/dotfiles
          paths:
            - terminal
            - graphical/default
            - graphical/deb
          remote: gh:makkus/somethingorother

In this example, the 'dotfiles' folder is checked out from the specified remote on github (check out XXX for more information on url-expansion), and the freckles plugins that support this, will look in the '~/dotfiles/terminal', '~/dotfiles/graphical/default' and '~/dotfiles/graphical/deb' folders for subfolders (like: 'emacs', which would contain a '.emacs.d' directory) to process (instead of subfolders of the base_dir). In this example, there is a 'debian'-specific subfolder that would only be used on Debian-based systems, and it would automatically set the package manager to use to 'apt' (more information on how the package manager is selected in the *install* module can be found here: XXX)
