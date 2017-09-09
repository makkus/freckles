##########
python-dev
##########

The `python-dev` adapter downloads folders that contain python code that can be installed via either ``pip`` or ``setuptools``. It'll install potential system dependencies, creates a python virtualenv and installs python development dependencies into that virtual environment. Alternatively the adapter can use *conda*.

Usage
*****

.. code-block:: console

   freckles dotfiles [OPTIONS] -f <freckle_url_or_path>

At least one path or url to a freckle needs to be provided (multiple paths can be supplied by simply providing multiple ``--freckle`` options)

Options
=======

``--freckle``
    the path or url that points to a 'dotfiles' freckle

``--pkg-mgr``
    the package manager and way of creating the virtual environment to use. defaults to "auto", which uses system dependencies and python virtualenv. The other option is ``conda``.

``--python-version``
    the version of python to use for the virtual (or conda) environment, defaults to '3'

Metadata
========

Metadata that can be provided within the *freckle* itself, either via the ``.freckle`` file in the root of the *freckle* directory, or via marker files.

TODO: link to package list format

vars
----

``packages``
    a list of non-python dependency packages

``python_version``
    the version of python to use for the virtual (or conda) environment, defaults to '3'

``requirements_files``
    a list of filenames that contain python dependencies for development (or doc generation, etc.). If not specified, all files in the project folder that match the regex ``.*requirements.*txt$`` are used

``setup_command``
    whether to use ``pip`` or ``setuptools`` to install the project into the virtual environment, defaults to ``pip``

``setuptools_command``
    if ``setuptools`` is used as ``setup_command``, this can be used to determine which command to use for the ``python setup.py <command>`` command. Defaults to ``develop``.


*freckle* folder structure
--------------------------

.. code-block:: console

   <freckle_root>
           ├── .freckle (optional)
           ├── [requirements<XXX>.txt]  (optional)
           ├── setup.py
           ├── [setup.cfg]
           .
           .
           ├── <python_src_folder>
           │              ├── [__init__.py]
           │              ├── <python_src_file_1>
           │              ├── <python_src_file_2>
           .              ├─        ...
           .                        ...
           .                        ...

Additional files and markers
----------------------------

If the ``requirements_files`` variable is not set, all files that match the regex ``.*requirements.*txt$`` are used and their content installed into the virtual environment as python dependencies.


Example ``.freckle`` files
--------------------------

simple python 2 project, using ``pip``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As the ``setup_command`` var is not specified, it'll fall back to ``pip``, meaning ``pip install -e .`` will be used to install the source code into the development virtual env.

.. code-block:: yaml

    python-dev:
       python_version: 2.7

simple python 3 project, using ``setuptools``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As the ``setup_command`` var is specified, ``setuptools`` will be used, meaning ``python setup.py develop`` will be used to install the source code into the development virtual env.

.. code-block:: yaml

    python-dev:
       python_version: 3
    setup_command: setuptools


Examples
********

Below are some more exmaples with a detailed explanations to illustrate how to use the *python-dev* adapter.

``.freckle`` file for *freckles* itself
=======================================

This is the configuration *freckles* itself uses. Because of Ansible still not being fully supported on Python 3, *freckles* also uses Python 2. Ansible also has a few non-python dependencies that are required to build the ``cryptography`` python library, which can be installed either via the system package manager, or we use conda to get the compiled ``cryptography`` and ``pycrypto`` dependencies directly. Mac OS X (homebrew) does not need any extra system dependencies installed.

.. code-block:: yaml

    python-dev:
       python_version: 2.7

       setup_command: "pip"
       requirements_files:
          - requirements_dev.txt
       packages:
          - pycrypto-related:
              pkgs:
                debian:
                  - libssl-dev
                  - libffi-dev
                  - libsqlite3-dev
                conda:
                  - cryptography
                  - pycrypto
                other: omit
