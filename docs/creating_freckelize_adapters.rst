############################
Creating freckelize adapters
############################

Quick-start
***********

*frecklelize adapters* use *Ansible's* configuration format (facilitating *yaml*), similar to how to create Ansible playbooks and tasks for roles. I'll assume you have some experience with *Ansible* here. If that is not the case, maybe check out the `Ansible documentation <http://docs.ansible.com/ansible/latest/playbooks_intro.html>`_ before continuing here.

*freckles* comes with a *frecklecute* (called `'create_adapter' <https://github.com/makkus/freckles/blob/master/freckles/external/frecklecutables/create-adapter>`_ that can help you creating a *freckles adapter* stub in ``$HOME/.freckles/adapters/<adapter_name>``:

.. code-block:: console

   frecklecute create-adapter <adapter_name>

For example, let's create an adapter that can handle projects that use Vagrant_. The adapter will, after checking out of the *freckle*, install *Vagrant* (if it is not already installed), then read the *freckle* metadata to determine whether any *Vagrant plugins* need to be installed, then installs those.

.. code-block:: console

   frecklecute create-adapter vagrant-dev-example

To see that our adapter-stub was created, we can run the *freckles* help:

.. code-block:: console

   $ freckles --help

   Usage: freckles [OPTIONS] ADAPTER1 [ARGS]... [ADAPTER2 [ARGS]...]...

   Downloads a remote dataset or code (called a 'freckle') and sets up
   your local environment to be able to handle the data, according to
   ...
   ...

                        * more help output *

   ...
   ...
   --version                       prints the version of freckles
   --help                          Show this message and exit.

   Commands:
     debug-freckle        helper adapter, for developing other adapter
     dotfiles             installs packages, stows dotfiles
     python-dev           prepares a python development environment
     vagrant-dev-example  adapter-stub, please fill in the fields as
                          approriate

     freckles is free and open source software, for more information
     visit: https://docs.freckles.io

As you can see, the ``vagrant-dev-example`` profile is created and ready to be used by *freckles*. By default it only contains a few debug tasks, which is helpful to see which metadata variables are present to be used by our adapter.

Let's clean up the help output first before we continue. To do that, edit the file ``$HOME/.freckles/adapters/vagrant-dev-example/vagrant-dev-example.freckle-adapter``, and change the ``doc`` key like like so:

.. code-block:: shell

   doc:
     help: freckle adapter to prepare a host machine for a Vagrant (https://www.vagrantup.com)
     short_help: installs Vagrant and, (optional) required plugins

To see the effect, just run ``freckles --help`` again.

I've create an example *freckle* repository with some example metadata to help developing this adapter, https://github.com/makkus/vagrant-dev-example-freckle. To see what metadata the adapter has available at runtime, we can run the adapter in it's initial state:

.. code-block:: shell

   freckles -o skippy vagrant-dev-example -f gh:makkus/vagrant-dev-example-freckle

   PLAY [name] ********************************************************************

   TASK [Gathering Facts] *********************************************************
   ok: [localhost]
   ...

                * more output *

   ...
   TASK [makkus.freckles : debug freckle vars] ************************************
   ok: [localhost] => {
       "freckle_vars": {
           "vagrant_plugins": [
               "vagrant-bindfs"
           ]
       }
   }

We use the ``skippy`` output format as the default one wouldn't display any debug variables.

First order of business is to make sure *Vagrant* is installed. Since *freckles* supports the processing of multiple *freckle* folders in the same run, but it is not necessary to ensure *Vagrant* is installed for every one of those processing iterations, we put the required directives in the file called ``vagrant-dev-example.freckle-init`` (in ``$HOME/.freckles/adapters/vagrant-dev-example``). We replace the existing content of the ``vagrant-dev-example.freckle-init`` file with:

.. code-block:: yaml

   - name: checking whether to install Vagrant
     include_role:
       name: makkus.install-vagrant

This uses an already existing Ansible role that is (conveniently) shipped with *freckles*.

Now we can run *freckles* again, and see whether it does in fact install *Vagrant*:

.. code-block:: console

   $ freckles vagrant-dev-example -f gh:makkus/vagrant-dev-example-freckle

     * starting tasks (on 'localhost')...
      * applying profile(s) to freckle(s)...
        - checking out freckle(s) =>
            - https://github.com/makkus/vagrant-dev-example-freckle.git => ok (no change)
        - checking whether to install Vagrant => ok (no change)
        - creating cache download dir => ok (changed)
        - downloading Vagrant => ok (changed)
        - installing Vagrant Debian package => ok (changed)
        - deleting downloaded Vagrant install package => ok (changed)
        - debug freckle path => ok (no change)
        - debug freckle vars (raw) => ok (no change)
        - debug freckle vars => ok (no change)
        => ok (changed)

Looks good! Those last 3 debug statements are the ones still present in the ``vagrant-dev-example.freckle-tasks`` file. Let's edit that next, and make the adapter install all the *Vagrant* plugins that are specified in the ``.freckle`` metadata file. For our example repository we know this is one plugin, 'vagrant-bindfs'.

.. code-block:: yaml

   - name: install vagrant plugins
     install:
       pkg_mgr: vagrant_plugin
       packages:
         - "{{ item }}"
     with_items:
       - "{{ freckle_vars.vagrant_plugins | default([]) }}"

(You might not recognize the ``install`` Ansible module, as it's custom written to be used with *freckles*. Check out :doc:`this page </install_module>` for more information.

Let's run the whole thing again:

.. code-block:: yaml

   freckles vagrant-dev-example -f gh:makkus/vagrant-dev-example-freckle

   * starting tasks (on 'localhost')...
    * applying profile(s) to freckle(s)...
      - checking out freckle(s) =>
          - https://github.com/makkus/vagrant-dev-example-freckle.git => ok (no change)
      - checking whether to install Vagrant => ok (no change)
      - install vagrant plugins =>
          - vagrant-bindfs (using: vagrant_plugin) => ok (changed)
      => ok (changed)

Voilà! Now we can prepare hosts for all *freckle* folders that contain code that needs *Vagrant* and potentially some *Vagrant plugins*!

More documentation to be written. Stay tuned!

.. _vagrant: https://www.vagrantup.com

