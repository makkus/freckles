=====
Usage
=====

The internal ``help``
---------------------

.. code-block:: console

   freckles --help

To see the options for each sub-command, use:

.. code-block:: console

   freckles <subcommand> --help

``apply``-ing configurations
----------------------------

``apply`` is the main command to be used with *freckles*. It takes one or more configuration files or urls to configuration files, and applies the environment that is described in those onto the machine where *freckles* is running.

.. code-block:: console

   freckles apply <config_url_or_path_1> [<config_url_or_path_2> <config_url_or_path_3> ...]

*freckles* configuration files are designed to be as simple to create as possible, while maintaining the ability to describe more complex setups by optionally supporting a more complex format. On this page we will only use the simple format, for more details on how to get the most out of it please check out the :ref:`configuration` section, as well as the usage :ref:`examples`.

Installing a few packages
+++++++++++++++++++++++++

For most simple use-cases, a single configuration file will be sufficient. *freckles* configurations are basically a list of tasks, and each task is of a certain type, and has it's own configuration. *freckles* supports several frequently used task types out of the box, but can be extended to use custom task types if necessary. For a list of existing task types, check here: `TBD <XXX>`_

The most commonly used task type would probably be the ``install`` one. Let's assume we only want to use *freckles* to install a few packages using the default package manager. The default package manager for Debian/Ubuntu is ``apt``, for RedHat/CentOS its ``yum``, and for Mac OS X we use ``homebrew``. If we only use one platform, and intend to use the default package manager of this platform, we don't need to specify anything, which makes the configuration file simpler to create, and easier to read.

Here is a config that will install the packages ``htop``, ``fortunes``, and ``zile`` on a Debian/Ubuntu system:

.. code-block:: console

   tasks:
     - install:
         packages:
            - htop
            - fortunes
            - zile

In this example, we have one task (of the ``install` type), the configuration for the task being a list of package names.

This configuration file (as well as all the following ones) can be found in the `main freckles git repository <https://github.com/makkus/freckles>`_, in the `examples <https://github.com/makkus/freckles/tree/master/examples>`_ folder: `https://github.com/makkus/freckles/examples/usage-simple-debian.yml <https://github.com/makkus/freckles/blob/master/examples/usage-simple-debian.yml>`_

Because *freckles* is designed to be run as the first command on a fresh install, it can directly download configuration files, without them having to be present locally. It can also use local files though.

Here are a few examples on how to run freckles to apply this configuration, using either a local file, or a remote one:

Local configuration file
........................

Assuming you downloaded the config file into your 'Downloads' folder, you can run *freckles* like so:

.. code-block:: console

   freckles apply ~/Downloads/usage-simple-debian.yml

Remote configuration file, full url
...................................

Alternatively, we can just provide the full url to the file:

.. code-block:: console

   freckles apply https://github.com/makkus/freckles/raw/master/examples/usage-simple-debian.yml

Remote configuration file, short github url
...........................................

Because it's convenient, and easier to remember, *freckles* also supports shortcut urls for files that live on github (other services will be supported in the future):

.. code-block:: console

   freckles apply gh:makkus/freckles/examples/usage-simple-debian.yml

First run output
................

Either of those commands will do the same, and the output will look something like this:

.. code-block:: console

   Preparing run #1
   Starting run #1

   Looks like we need a sudo password for some parts of the pipeline, this might interrupt the execution process, depending on how sudo is configured on this machine. Please provide your password below (if applicable).

   SUDO password:
   - task 01/03: apt -> install 'fortunes'	=> changed
   - task 02/03: apt -> install 'htop'	=> changed
   - task 03/03: apt -> install 'zile'	=> changed
   Run #1 finished: success

*freckles* tries to determine whether a sudo password is required (for example, some package managers need sudo, some other don't, some systems have passwordless sudo, some do not), and it will display the above message if it thinks it is. The password prompt is the underlying *ansible* playbook runs though.


Installing packages using a dotfile repository
++++++++++++++++++++++++++++++++++++++++++++++

This was easy, but most of the time we also have to worry about configurations we want to use on multiple boxes. There are several ways of doing that, each have their advantages and disadvantages. In theory *freckles* can support all of those methods, but at the moment only one is implemented, since that is the one I currently use, and it looks like a lot of other people do too, for example:

- https://alexpearce.me/2016/02/managing-dotfiles-with-stow/
- http://brandon.invergo.net/news/2012-05-26-using-gnu-stow-to-manage-your-dotfiles.html
- http://codyreichert.github.io/blog/2015/07/07/managing-your-dotfiles-with-gnu-stow/
- http://www.garin.io/dotfiles-with-stow

Basically, your dotfiles are all stored in a git repository (here's `mine <https://github.com/makkus/dotfiles>`_). The folder structure is like:

.. code-block:: console

   <base-dir>
       |
       |-- app1
       |    |-- .app1rc
       |
       |-- app2
       |    |-- .app2
       |          |-- app2config1
       |          |-- app2config2
       |
      etc

This makes for a nice and tidy organisation of all your dotfiles, and they don't get in each others way. In order to get the config files to the location the application expects it to, we use `GNU stow <https://www.gnu.org/software/stow/>`_. We point ``stow`` to our base directory, and tell it to symbolically link everything that is in one of the sub-folders of our base directory into the users home directory. ``stow`` is quite smart and can do that with a few different strategies, but I'll not get into those here. I recommend you look up how ``stow`` works, it's worth a read.

Since I manage my dotfiles using ``git`` and ``stow`` anyway, I figured we can re-use the folder structure we have already to install the packages that belong to our configurations. The only thing we need to do is to name the sub-folders like the package name on the platform we use. As an example, we'll using the emacs-like editor called ``zile`` which I find quite handy to quickly edit small text files. It uses a configuration file called ``.zile``, which needs to be located in the root of the home directory:

.. code-block:: console

   <base-dir>
       |
       |-- zile
       |     |-- .zile

If we cd into the dotfiles base-dir, and run stow with the ``zile`` argument, this happens:

.. code-block:: console

   $ cd ~/dotfiles
   $ stow zile
   $ ls -lah ~/.zile
   lrwxrwxrwx 1 markus markus 19 Apr 20 10:56 /home/markus/.zile -> dotfiles/zile/.zile
   $ _

I've prepared an example repository, containing an example zile config file `here <https://github.com/makkus/dotfiles-example>`_. We'll get *freckles* to checkout this dotfile directory into ``$HOME/dotfiles-example``, install all the packages that are named like the sub-folders contained in it (only one in this case, ``zile``), and then stow all the config files we need (again, only one). The config to do this looks like:

.. code-block:: console

   vars:
     dotfiles:
       - base_dir: ~/dotfiles-quickstart
         remote: https://github.com/makkus/dotfiles-example.git
   tasks:
     - checkout-dotfiles
     - install:
         use_dotfiles: true
     - stow

Applying this config, this is what will happen:

.. code-block:: console

   $ freckles apply example.yml
   Preparing run #1
   Starting run #1
   - task 01/01: checkout dotfiles 'https://github.com/makkus/dotfiles-example.git -> /home/markus/dotfiles-quickstart'	=> changed
   Run #1 finished: success
   Preparing run #2
   Starting run #2
   - task 01/02: apt -> install 'zile'	=> no change
   - task 02/02: stow - /home/markus/dotfiles-quickstart/ -> /home/markus 'zile'	=> changed
   Run #2 finished: success

Depending on your environment, it might have also asked for a sudo password again.

Notice how it says ``install 'zile' => no change``. This is because we already installed it earlier. Also, notice how the execution is split into two 'runs'. This is because *freckles* needs the up-to-date dotfile repository to exist before it can calculate which applications to install using the folder names within. If we would run all tasks in the same go, no application would be installed because no folder would exist yet (at the time of run preparation).

Also, in the ``install`` task we have an extra variable ``use_dotfiles``. This tells the ``install`` task to look at the ``dotfiles`` variable and use the dotfile repo described in it to calculate which applications to install (based on the sub-folder names, as mentioned above), in addition to the ``packages`` variable (which is empty in this case). This works because *freckles* merges variable dictionaries on top of each other, the closer to the task at hand the later the dict is merged, which means those variables take precedence if there is a conflict. In this example, this means that we give the ``install`` task 2 variables: ``dotfiles`` and ``use_dotfiles``.

If we check our home directory, we'll see the symbolic link ``stow`` created:

.. code-block:: console

   $ ls -lah ~/.zile
   lrwxrwxrwx 1 markus markus 30 Apr 20 03:06 /home/markus/.zile -> dotfiles-quickstart/zile/.zile


Let's go through the config example and try to understand how it works:

.. code-block:: console

   vars:
     dotfiles:
       - base_dir: ~/dotfiles-quickstart
         remote: https://github.com/makkus/dotfiles-example.git

This creates a variable called ``dotfiles``, which contains a list of dicts as values. The variable(s) created here apply to all ``tasks`` that are described subsequently. We could also give each task it's own set of variables, like so:

.. code-block:: console

   tasks:
     - checkout-dotfiles:
         dotfiles:
           - base_dir: ~/dotfiles-quickstart
             remote: https://github.com/makkus/dotfiles-example.git
     - install:
         dotfiles:
           - base_dir: ~/dotfiles-quickstart
             remote: https://github.com/makkus/dotfiles-example.git
         use_dotfiles: true
     - stow:
         dotfiles:
           - base_dir: ~/dotfiles-quickstart
             remote: https://github.com/makkus/dotfiles-example.git

In this case this doesn't make sense, since all tasks need the same ``dotfiles`` variable, and duplicating it would not make any sense.

In general, the tasks we describe are executed in the order they appear in the config file. So, here we checkout the dotfile repo, install all required packages, and finally stow all configurations.

Install packages and execute other tasks
++++++++++++++++++++++++++++++++++++++++

Now, let's merge both ways of installing packages, so we can have both packages that need as well as those that don't need configuration:

.. code-block:: console

   vars:
     dotfiles:
        - base_dir: ~/dotfiles-quickstart
          remote: https://github.com/makkus/freckles-quickstart.git

   tasks:
     - checkout-dotfiles
     - install:
         use_dotfiles: true
         packages:
           - htop
           - fortunes
           - fortunes-off
           - fortunes-mario
     - stow
     - create-folder: ~/.backups/zile

In addition to the ``checkout-dotfiles``, ``install`` and ``stow`` tasks, we introduce a new task type here: ``create-folder``. This does exactly what you expect it to do: creates a folder, using a string or list of strings with folder paths. If a folder already exists, it will do nothing.

In this case, we need the folder ``$HOME/.backups/zile`` because it is configured in the .zile configuration file in our dotfile directory. ``zile`` itself does not create this folder, and can't create backups if it doesn't exist.

Install packages on different platforms
+++++++++++++++++++++++++++++++++++++++

Depending on your requirements, sometimes you might want to re-create the same environment on different platforms. Say, your development machine is running Mac OS X, but you often use virtual machines running Ubuntu (maybe using Vagrant) as well. One of the problems here is that package names sometimes differ no different platforms. In our last example, we installed the applications ``htop``, ``fortunes`` (including a few debian-specific 'plugins` for it), and ``zile``. ``htop`` and ``zile`` are usually named the same on most platforms I came across, but ``fortunes`` is named is called ``fortune-mod`` on RedHat, and ``fortune`` on homebrew for Mac OS X.

*freckles* can handle this, by supporting an optional configuration format for the ``install`` plugin which deals with more complex contexts. You won't need this too often I'd imagine, but it's simple enough to use to be included in this basic usage guide.

For packages that are named the same, we don't need to do anything in particular, we can leave their config as it is. For the fortune mod we have to tell *freckles* the name of the package(s) on the respective platform:

.. code-block:: console

   - install:
       use_dotfiles: true
       packages:
         - epel-release:
             pkgs:
               yum:
                 - epel-release
         - htop
         - fortune:
             pkgs:
               apt:
                 - fortunes
                 - fortunes-off
                 - fortunes-mario
               yum:
                 - fortune-mod
               homebrew:
                 - fortune

As you can see, *freckles* assumes the package name is the string if the list item under ``packages`` is a string. If the list item is a dict, it will look for a key called ``pkgs`` and look up the package manager that is used on the system *freckles* is running on using its key. In the case of a debian-based system, we install 3 packages. Those additional packages don't exist on RedHat or in Homebrew, which is why we don't worry about them. Also, notice how we install the ``epel-release`` package. This only exists for RedHat-based systems, and is needed to enable some extra repositories without which we wouldn't be able to install some of our specified applications. Since the respective ``pkgs`` dict does not have entries for ``deb`` or ``homebrew``, this is ignored on those platforms.

For a complete config file that does all of the things we talked about so far, check out: `quickstart.yml <https://github.com/makkus/freckles/blob/master/examples/quickstart.yml>`_
