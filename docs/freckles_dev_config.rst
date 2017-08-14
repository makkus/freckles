Freckles development config
===========================

This page two different ways to setup a development environment for *freckles*, using *freckles*.

Using conda
+++++++++++

This first config sets up a conda_ environment for *freckles*, containing all the requirements (apart from the ones described in the freckles `setup.py <https://github.com/makkus/freckles/blob/master/setup.py>`_ file). Once that is done, ``python setup.py develop`` is run in the project folder to finish of the setup. If conda is not installed yet it'll set that up as well, of course.

This is how to kick off the process:

.. code-block:: console

   freckles apply gh:makkus/freckles/examples/freckles-dev/conda.yml

And this is how the config file looks:

.. literalinclude:: ../examples/freckles-dev/conda.yml
   :language: yaml
   :caption: conda.yml
   :name: conda.yml

As you can see, it is fairly straightforward. the ``git-repo`` freck is used to checkout the *freckles* source, ``install-conda`` installs conda if not already present, then two ``shell`` commands are run to `create a conda environment from a environment.yml file <https://conda.io/docs/using/envs.html#use-environment-from-file>`_ and to setup the python project using setuptools. The ``shell`` tasks are invoking ansible directly, just forwarding the provided variables to the `shell ansible module <http://docs.ansible.com/ansible/shell_module.html>`_.

Also note the ``vars.project_repo`` and ``vars.project_dir`` variables used in this configuration. Those come in handy if you, for example, want to use a different directory than ``~/projects/freckles`` as destination for the *freckles* source checkout. Or you have cloned the repo and want to use your clone.

I'm not going to explain how the template expression:

.. code-block:: console

   {{ vars.project_dir | default('~/projects/freckles') }}

works in detail (check `here <XXX>`_ if you are interested). Basically this is using the same templating language and extensions ansible_ uses, so there should be plenty of information around.

*freckles*, so far, supports 2 'variable-sources':

- **vars**: variables that were defined in earlier configuration files (format: **vars**.<variable_name>)
- **env**: environment variables (format: **env**.<variable_name>, e.g. ``env.HOME``)

Now, how to actually change the defaults? At the time of writing, it is not possible to define a variable in the same file where it is used. This means we need to prepare a separate yaml file:

.. literalinclude:: ../examples/freckles-dev/vars.yml
   :language: yaml
   :caption: vars.yml
   :name: vars.yml

(Note, those are the same values as are set in the ``conda.yml`` file. Easy to see how to change them, though, I hope)

Because *freckles* overlays configuration values on subsequent config files, while keeping non-overlayed ones around, it is fairly easy to sort of augment the base ``conda.yml`` config:

.. code-block:: console

   freckles apply gh:makkus/freckles/examples/freckles-dev/vars.yml gh:makkus/freckles/examples/freckles-dev/conda.yml

Once this is finished, we can enter the conda environment like so:

.. code-block:: console

   source activate freckles-dev

or, if the path in your system is not setup properly yet:

.. code-block:: console

   source ~/.freckles/opt/conda/bin/activate freckles-dev



Using a Python virtualenv
+++++++++++++++++++++++++

What if we don't like *conda*, or just plain prefer a `python virtualenv <http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/>`_?

Easy. Well, not as easy as using conda, since we need to do a bit more legwork, but the config is still fairly straightforward:

.. literalinclude:: ../examples/freckles-dev/virtualenv.yml
   :language: yaml
   :caption: virtualenv.yml
   :name: virtualenv.yml

As you can see, we are re-using the ``vars.yml`` file we created in the *conda* section. We could also 'out-var' the virtualenv folder location since we have it in 3 different places in the file, but for the sake of this example I decided not to bother.

What is happening is fairly straightforward:

- checking out the *freckles* sources
- installing the requirements we need to setup a virtualenv, as well as those that *freckles* needs (even providing them for both *Debian* and *RedHat*-based systems)
- creating the virtualenv folder
- installing the python dependencies we need for development (listed in the ``requirements_dev`` file)
- setting up the project using *setuptools* (that step is the same as when using *conda*)

To set everything up that way, we need to issue:

.. code-block:: console

   freckles apply gh:makkus/freckles/examples/freckles-dev/vars.yml gh:makkus/freckles/examples/freckles-dev/virtualenv.yml

Although, of course if we are happy with the defaults we could just omit calling the ``vars.yml`` file.

Anyway, once the *freckles* run finished, you can enter the *freckles-dev* virtualenv by issuing:

.. code-block:: console

   source ~/.freckles/opt/venv_freckles_dev/bin/activate

.. _conda: https://conda.io
.. _ansible: https://ansible.com
