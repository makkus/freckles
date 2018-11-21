========
freckles
========


.. image:: https://img.shields.io/pypi/v/freckles.svg
           :target: https://pypi.python.org/pypi/freckles
           :alt: pypi

.. image:: https://readthedocs.org/projects/freckles/badge/?version=latest
           :target: https://freckles.readthedocs.io/en/latest/?badge=latest
           :alt: Documentation Status

.. image:: https://gitlab.com/freckles-io/freckles/badges/develop/pipeline.svg
           :target: https://gitlab.com/freckles-io/freckles/pipelines
           :alt: pipeline status

.. image:: https://pyup.io/repos/github/makkus/freckles/shield.svg
           :target: https://pyup.io/repos/github/makkus/freckles/
           :alt: Updates

.. image:: https://gitlab.com/freckles-io/freckles/badges/develop/coverage.svg
           :target: https://gitlab.com/freckles-io/freckles/commits/develop
           :alt: coverage

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
           :target: https://github.com/ambv/black
           :alt: codestyle


**DevOps for the rest of us!**

A framework for composable, declarative scripting.

**freckles** helps you save time by automating tasks you usually don't automate (unless you already do -- in which case you might still be
interested in a few of **freckles**'s features that can make your life easier):

- re-use the included task-descriptions, as well as ones curated by the community
- install fairly complex to setup services with one only command
- create a repository of your own often used tasks, and make them composable
- re-use your setup configurations for development, CI and production
- create and share re-usable deploy configurations
- free yourself from depending on provider-specific technologies

Examples
--------

To see what category of tasks I'm talking about, here are a few examples.

Some of those examples need either root permissions, or an admin user who has password-less sudo setup. Also, most
of this is only tested on Debian Stretch. For anything involving the generation of https certificates, DNS needs to be setup in advance.

Creating a file with a certain content
++++++++++++++++++++++++++++++++++++++

This command creates a file with a 'hello world' content string. It also creates all parent folders (if necessary):

.. code-block::

    $ frecklecute ensure-file-content

    ╭─ starting: 'file-exists-with-content'
    ├╼ connector: nsbl
    │  ├╼ host: localhost
    │  │  ├╼ starting playbook
    │  │  │  ╰╼ ok
    │  │  │  ├╼ checking if parent folder exists
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ creating parent directory for: /tmp/freckles/example.file'
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ writing content to file: /tmp/freckles/example.file
    │  │  │  │  ╰╼ ok
    │  │  │  ╰╼ ok
    │  │  ╰╼ ok
    │  ╰╼ ok
    ╰─ ok


This would also work on another host, all you need to do is specify the ``--host <username>@<hostname>`` flag.


Docker
++++++

Installing Docker on a machine is not as straightforward and quick as I think it should be. This is how you do it with *freckles*:

.. code-block::

    frecklecute pkg-docker-installed

(doesn't work for Ubuntu cosmic yet -- no repository yet)


Setting up Wordpress
++++++++++++++++++++

Creating files and installing simple applications is boring thoug, lets deploy a full wordpress site, using MariaDB, Apache (or, if you want, Nginx) and LetsEncrypt certificate.

As a hosting provider you can use any of the many available ones, e.g. DigitalOcean, Hetzner, Amazon, etc...

.. code-block::

     frecklecute -h root@dev.cutecode.co --community wordpress-single-site --host dev.cutecode.co \
                 --wp-title example-site --wp-admin-email info@cutecode.co

To see all supported options of this command, use ``frecklecute --community wordpress-single-site --help``. Notice the ``--community`` flag. This points to a collection of community-curated task 'recipes': https://gitlab.com/frecklets

Discourse
+++++++++

Or maybe you want to setup an instance of the `Discourse forum service <https://discourse.org>`_? Also easy:

.. code-block::

    frecklecute -h root@frnds.of.frkl.io setup-discourse --domain frnds.of.frkl.io --admin-email info@frnds.of.frkl.io
                --smpt-server smtp.postmarkapp.com --smtp-port 587 --smtp-user 'xxxxx' --smtp-password 'xxxxx'

For that to work, you need to have setup your domain and email provider beforehand.

Links
-----

This here ``README`` only contains very basic information. *freckles* is a fairly feature-full framework, and has a lot
of bells and whistles. For more in-depth information, visit one of the following links:

- `Documentation <https://docs.freckles.io>`_ ( work in progess )
- `Homepage <https://freckles.io>`_ ( work in progress - currently this is only my old blog )

Installation
------------

.. code-block::

    curl https://freckles.sh/install | bash

For more install options, visit: [Installing freckles](https://docs.freckles.io/en/latest/installation.html)

Usage
-----

The main artefacts *frecklets* works with are called *frecklecutables*. A *frecklecutable* is a list of one or several
tasks. It defines a set of valid inputs, and should yield, if called with the same parameters, the same result on the
target host.

General help & supported frecklecutables
++++++++++++++++++++++++++++++++++++++++

To see a list of included supported options, as well as (featured) available frecklecutables, do:

.. code-block::

    frecklecute --help

    Usage: frecklecute [OPTIONS] COMMAND [ARGS]...

    Options:
      -c, --config TEXT     select config profile(s)
      --community           allow resources from the freckles community repo
      -r, --repo TEXT       additional repo(s) to use
      -h, --host TEXT       the host to use
      -o, --output TEXT     the output format to use
      -v, --vars VARS_TYPE  additional vars, higher priority than frecklet vars,
                            lower priority than potential user input
      -e, --elevated        indicate that this run needs elevated permissions
      -ne, --not-elevated   indicate that this run doesn't need elevated
                            permissions
      --no-run              create the run environment (if applicable), but don't
                            run the frecklecutable
      --version             the version of freckles you are using
      --help-all            Show this message, listing all possible commands.
      --verbosity LVL       Either CRITICAL, ERROR, WARNING, INFO or DEBUG
      --help                Show this message and exit.

    Commands:
      create-admin-user               creating admin user
      create-file                     ensures a file exists
      create-folder                   ensures a folder exists
      create-group                    ensures a group exists
      create-parent-folder            ensures the parent folder of a path exists
      create-user                     ensures a user exists on a system
      download-file                   downloads a file
      ensure-file-content             ensures a file exists and its content is the
    ...
    ...
    ...

This list doesn't contain all included frecklecutables, only ones that are marked as 'featured' in their metadata. To the
the full list, issue:

.. code-block::

    frecklecute --help-all

frecklecutable-specific help
++++++++++++++++++++++++++++

Each frecklecutable has it's own help output. You can get to it via:

.. code-block::

    frecklecute <frecklecutable_name> --help

For example:

.. code-block::

    frecklecute download-file --help

    Usage: frecklecute download-file [OPTIONS] URL

      Downloads a file, creates intermediate destination directories if necessary.

      If no 'dest' option is provided, the file will be downloaded into
      '~/Downloads'.

      This uses the [Ansible get_url module](https://docs.ansible.com/ansible/la
      test/modules/get_url_module.html), check it's help for more details.

    Options:
      --group GROUP  the group of the target file
      --owner USER   the owner of the target file
      --dest DEST    the destination file (or directory).   [default: ~/Downloads/]
      --become-user  the user to download as
      --mode MODE    the mode the file should have, in octal (e.g. 0755)
      --force        whether to force download/overwrite the target.
      --help         Show this message and exit.

Executing a frecklecuteable
+++++++++++++++++++++++++++

Each frecklecutable can have a set of arguments, both required and optional. Some of those can have default values.

In the ``download-file`` example  above, the ``URL`` argument is required, and the ``--dest`` option has a default value.

If we wanted to download a file into the default ``Downloads`` directory, all we would have to do is:

.. code-block::

    frecklecute download-file https://frkl.io/images/frkl-logo-black.svg

A more complex use-case would be to download the file into a custom directory, and change the permissions to a certain user.
This frecklecutable will create the user if it doesn't already exit:

.. code-block::

    frecklecute download-file --become-user root --owner www-data --dest /var/www/html/logo.svg https://frkl.io/images/frkl-logo-black.svg

Here we need to set the ``--become-user`` option, because our normal user wouldn't have permissions to create a new
user if necessary, and to create a file in ``var/www/html/``.

License
-------

Parity Public License 3.0.0

Please check the `LICENSE <LICENSE>`_ file in this repository (it's a short license!), https://freckles.io/licensing (not written yet) and the `README.rst file <contributing/README.rst>`_ in the ``contributing`` folder.
