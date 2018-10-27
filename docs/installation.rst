.. highlight:: shell

###################
Bootstrap / install
###################

There are a few different ways to bootstrap *freckles*. Depending on the state of your box, your proficiency and your general trust in random people on the internet, you can choose one of the methods below.

Bootstrap & execution in one go ("inaugurate")
**********************************************

The main way of bootstrapping *freckles* is by utilizing *inaugurate*, a bash script I wrote for *freckles* but decided to make into it's own project because I figured it might be worth a shot creating a sort of 'generic bootstrap script'.

For how it exactly works, and why you should or should not trust it, head over `to it's homepage <https://github.com/makkus/inaugurate/>`_. This method of bootstrapping is the easiest, and fricktionlessest. One of the main reasons for creating *freckles* was that I wanted a way to setup a new box (physical or virtual) by executing only one (easy to remember) line on a commandline terminal. *inaugurate* provides that functionality.


Description
===========

*inaugurate* supports two modes of install: either using *user*, or using *root* permissions. Although both methods achieve the same result, they go about it a bit differently. Both methods are explained in detail further below.

In this initial example we'll bootstrap *freckles* using *user* permissions, and then execute it directly, calling its help function. When used in anger, you'll probably point it to a *freckle* git repo, and let it do its thing directly, but for the purpose of this we'll not let it make any changes to our system (except for the install itself, obviously).

Here's the (base) command you'll have to execute to bootstrap & execute the included ``frecklecute`` command.

.. code-block:: console

    curl https://freckles.sh | bash -s -- frecklecute --help

Or, if you don't have `curl`, but `wget` installed on your box:

.. code-block:: console

   wget -O - https://freckles.sh | bash -s -- frecklecute --help

Alternatively, if you prefer or if the command you want to execute requires interactive input, you can use either of:

.. code-block:: console

   bash <(curl https://freckles.sh) frecklecute -f blueprint:static-website -t /var/lib/freckles

or

.. code-block:: console

    bash <(wget -O- https://freckles.sh) frecklecute -f blueprint:static-website -t /var/lib/freckles

Once you executed either one of the above commands successfully, you'll have *freckles* installed on your system. It'll have put a line in ``~/.profile`` to add it's path to the session PATH, so the next time you login (or do a ``source ~/.profile``) it'll be available. From then on all you need to type is:

.. code-block:: console

   frecklecute --help

Below a few more details on the two ways of bootstrapping *freckles* using *inaugurate*:

inaugurate (without elevated permissions)
-----------------------------------------

This is the default way of bootstrapping *freckles*. It will create a self-contained installation (under ``$HOME/.local/share/inaugurate/``), using conda_ to install requirements and create its working environment.

Commands
--------

Using `curl`:

.. code-block:: console

   curl https://freckles.sh | bash -s -- frecklecute <args>

Using `wget`:

.. code-block:: console

   wget -O - https://freckles.sh | bash -s -- frecklecute <args>

The install process can be influenced with environment variables, more details can be found in the `inaugurate documentation <https://github.com/makkus/inaugurate#environment-variables>`_.

What does this do?
^^^^^^^^^^^^^^^^^^

This installs the conda_ package manager (miniconda_ actually). Then it creates a `conda environment`_ called 'inaugurate', into which *freckles* along with its dependencies is installed.

Everything that is installed (about 450mb of stuff) is put into the ``$HOME/.local/share/inaugurate/conda/envs/inaugurate`` folder, which can be deleted without affecting anything else (except you did install some other applications using `conda`, those might be deleted too).

A line will be added to ``$HOME/.profile`` to add ``$HOME/.local/bin`` to the users ``$PATH`` environment variable.


Inaugurate (with elevated permissions)
--------------------------------------

This is a quicker (and leaner) way to bootstrap *freckles*, as 'normal' distribution packages are used to install dependencies. The size of the ``$HOME/.local/share/inaugurate`` folder will be smaller, ~70mb -- systems packages are adding to that in other parts of the system though. The *freckles* install itself is done in a *virtualenv* using `pip`. Root permissions are required.

Commands
^^^^^^^^

Using `curl`:

.. code-block:: console

   curl https://freckles.sh | sudo bash -s -- frecklecute <args>

Using `wget`:

.. code-block:: console

   wget -O - https://freckles.sh | sudo bash -s -- frecklecute <args>

The install process can be influenced with environment variables, more details can be found in the `inaugurate documentation <https://github.com/makkus/inaugurate#environment-variables>`_.

What does this do?
^^^^^^^^^^^^^^^^^^

This installs all the requirements that are needed to create a Python virtualenv for *freckles*. What exactly those requirements are differs depending on the OS/Distribution that is used (check the :ref:`Install manually via pip` section for details). Then a Python virtual environment is created in ``$HOME/.local/share/inaugurate/virtualenvs/inaugurate`` into which *freckles* and all its requirements are installed (~70mb).

A line will be added to ``$HOME/.profile`` to add ``$HOME/.local/bin`` to the users ``$PATH`` environment variable.

Supported platforms
===================

Those are the platforms I have tested so far, others might very well work too. I did my development mainly on Debian-based systems, so other Linux distributions might not (yet) be up to scratch:

- Linux

  - Debian
  - Ubuntu
  - CentOS

- Mac OS X

  - El Capitan
  - Sierra
  - High Sierra

- Windows

  - Windows 10 (Windows subsystem for Linux) -- not tested/working yet


Install manually via ``pip``
****************************

If you prefer to install *freckles* from pypi_ yourself, you'll have to install a few system packages, mostly to be able to install the ``pycrypto`` and ``cryptography`` packages when doing the ``pip install``.

Requirements
============

Ubuntu/Debian
-------------

.. code-block:: console

   apt install build-essential git python-dev python-virtualenv libssl-dev libffi-dev stow

RedHat/CentOS
-------------

.. code-block:: console

   yum install epel-release wget git python-virtualenv stow openssl-devel stow gcc libffi-devel python-devel openssl-devel

MacOS X
-------

We need Xcode. Either install it from the app store, or do something like:

.. code-block:: console

    touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress;
    PROD=$(softwareupdate -l |
           grep "\*.*Command Line" |
           head -n 1 | awk -F"*" '{print $2}' |
           sed -e 's/^ *//' |
           tr -d '\n');
    softwareupdate -i "$PROD" -v;


We also need to manually install pip:

.. code-block:: console

    sudo easy_install pip


Install *freckles*
==================

Ideally, you'll install *freckles* into its own virtualenv. But if you read this you'll (hopefully) know how to do that. Here's how to install it system-wide (which I haven't tested, to be honest, so let me know if that doesn't work)

.. code-block:: console

   sudo pip install --upgrade pip   # just to make sure
   sudo pip install freckles

Optionally, if necessary (if you didn't do a systemwide install) add *freckles* to your PATH. for example, add something like the following to your ``.profile`` file (obviously, use the location you installed *freckles* into, not the one I show here):

.. code-block:: console

   if [ -e "$HOME/.virtualenvs/freckles/bin" ]; then export PATH="$HOME/.virtualenvs/freckles/bin:$PATH"; fi


Install using an Ansible installation
*************************************

Another option is to install Ansible following their instructions: http://docs.ansible.com/ansible/intro_installation.html

Then, after that is done, install the ``freckles`` python package via pip in either a virtualenv, or system-wide.

.. _conda: https://conda.io
.. _inaugurate: https://github.com/makkus/inaugurate
.. _miniconda: https://conda.io/miniconda.html
.. _`conda environment`: https://conda.io/docs/using/envs.html
.. _pypi: https://pypi.python.org
.. _stow: https://www.gnu.org/software/stow
.. _`stow part of the bootstrap script`: https://github.com/makkus/freckles/blob/master/bootstrap/freckles#L218

