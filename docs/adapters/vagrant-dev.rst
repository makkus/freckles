###########
vagrant-dev
###########

The `vagrant-dev` adapter downloads folders that contain a project which is being developed using `vagrant <https://www.vagrantup.com>`_. It'll install *vagrant* itself if not yet installed, as well as per-project *provisioner* dependencies (e.g. the Virtualbox package) *vagrant plugins*.

Usage
*****

.. code-block:: console

   freckelize vagrant-dev [OPTIONS] -f <freckle_url_or_path>

At least one path or url to a freckle needs to be provided (multiple paths can be supplied by simply providing multiple ``--freckle`` options)

Options
=======

``--freckle``
    the path or url that points to a 'python-dev' freckle

Metadata
========

Metadata that can be provided within the *freckle* itself, either via the ``.freckle`` file in the root of the *freckle* directory, or via marker files.

TODO: link to package list format

vars
----

``providers``
    a list of providers to install (currently only 'virtualbox' is supported)

``vagrant_plugins``
    a list of vagrant plugins to install


*freckle* folder structure
--------------------------

.. code-block:: console

   <freckle_root>
           ├── .freckle (optional)
           ├── Vagrantfile
           .
           .
           ├── project_file_1
           ├── project_file_2
           .                        ...
           .                        ...

Additional files and markers
----------------------------

n/a

(Later on we might parse the Vagrantfile itself for required plugins/provisioners.


Example ``.freckle`` files
--------------------------

simple Virtualbox vagrant project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    provisioners:
       - virtualbox

simple virtualbox vagrant project with proxyconf plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    provisioners:
       - virtualbox
    vagrant_plugins:
       - vagrant-proxyconf

