#######################
Writing frecklecutables
#######################

.. note::

    This is work in progress, and a lot of stuff is still missing

.. note::

    Most of the following assumes you have a basic understanding of yaml, as well as Ansible

Overview
********

What is a *frecklecutable*
==========================

A *frecklecutable* is a yaml file, with at least the ``tasks`` key in the yaml root (and a list of tasks as value of that key), that does not have a '.' (dot) in it's file name. The building blocks of a *frecklecutable* are:

- all available `Ansible modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_
- all available Ansible roles from `Ansible galaxy <https://galaxy.ansible.com/>`_
- all other Ansible modules or roles that are available and configured on the machine *frecklecute* is running on
- any task alias that either ships with *freckles*, or is defined by the user

Here's a minimal example of a *frecklecutable* called ``update``, which updates the *freckles* package itself:

.. code-block:: yaml

   doc:
     help: updates freckles itself
   tasks:
     - update-freckles

The main element of a *frecklecutable* is it's task list, defined under the ``tasks`` key. The value of this key is a list of tasks. Each of those tasks can either be a string, or a dictionary. Before I continue with task lists, we need to learn about *task names* and *task types* though, as they are quite central to the whole thing.

Task items
----------

The most important element to an item in a task list is the kind of task it is (the *task type*). There are 3 types of tasks:

Ansible module
^^^^^^^^^^^^^^

Ansible, by default, comes with a big amount of so-called 'modules': `official Ansible modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_

An Ansible module is a (mostly Python, but can be written in other languages too) script that does one thing, in an idempotent way (which means, if you run the same thing twice, the state of the host machine after the 2nd run won't be different than after the 1st run). Ansible modules mostly concentrate on doing one thing, providing configuration options for all conceivable situations.

For example, have a look at the `lineinfile module <http://docs.ansible.com/ansible/latest/lineinfile_module.html>`_. It ensures that a certain line is present (or not present) in a text file. Or the `get_url module <http://docs.ansible.com/ansible/latest/get_url_module.html>`_, which ensures that a file is downloaded to a certain location. There are too many modules to even give a rough overview quickly here, but rest assured, it is very likely that there exists an Ansible module for whatever you need to do.

Ansible role
^^^^^^^^^^^^

Ansible also supports 'roles', which basically are lists of module calls, collected to achieve specific goals. For example, `install nginx on a server <https://galaxy.ansible.com/geerlingguy/nginx/>`_, or `prepare a workstation for web development <https://galaxy.ansible.com/bbatsche/Base/>`_.

Similar to modules, roles can be configured to do the task they are created to do differently, depending on the situation.

Ansible distributes those roles via a website called `Ansible galaxy <https://galaxy.ansible.com>`_, and it provides a helper tool (``ansible-galaxy``) to download those roles to the machine that runs Ansible.

Task alias
^^^^^^^^^^

A *task alias* can either point to a module or role, and contains additional metadata. Task *aliases* are defined in files called ``task-aliases.yml``. Here's a part of the one that ships with *freckles*:

.. code-block:: yaml

     - update-freckles:
         meta:
           task-type: ansible-role
           task_desc: updating freckles
           task-name: makkus.install-freckles
           task-roles:
             - makkus.install-conda
         vars:
           update: true
           install_method: auto
     - create-folder:
         meta:
            default-key: path
            with_items: path
            task-desc: creating folder(s)
            task-name: file
            var-keys:
              - state
              - path
              - attributes
              - group
              - mode
              - owner
              - recurse
              - selevel
              - serole
              - setype
              - seuser
         vars:
            state: directory

This defines two aliases: one called ``update-freckles`` which calls a role called 'makkus.install-freckles', with a few default variables, and one called ``create-folder``, which calls an Ansible module called 'file' and basically creates a folder. Who'd have thought, right?

More on aliases and how to create/include them in your environment can be found in the :doc:`freckles_repos` page.

Task configuration
------------------

Every task's (be it module or role or alias) purpose is to alter the state of the machine it is running on, in some way or other. The definition of the desired state is either inherent in the task itself (e.g. 'installed nginx webserver' for the `geerlingguy.nginx <https://galaxy.ansible.com/geerlingguy/nginx/>`_ role), or provided as configuration parameters (e.g. the path of a to-be-created folder for the `ansible file module <http://docs.ansible.com/ansible/latest/file_module.html>`_). Most of the time it is a mix of the two, and a task has several configuration options.

Ansible provides ways to 'overlay' variables to enable using the same tasks/roles for different machines/situations. As *freckles* only deals with one machine, it can afford to be a bit less powerful and complex than Ansible itself.

So, for *frecklecute*, there are 3 locations variables can be provided:

- as a dictionary provided directly to a task item
- via the ``vars`` key in a *frecklecutable*
- via the commandline (issue ``frecklecute <frecklecutable_name> --help`` to see each *frecklecutables* options


Let's take the example of ``create-folder``, which is a task alias that ships with *freckles* (see above). We need to provide a path so running the task makes any sense. Let's try all the options:

via dictionary
^^^^^^^^^^^^^^

.. code-block:: yaml

   tasks:
     - create-folder:
         path: ~/dict_folder

This is the simplest case, and the least ambivalent. Every task gets it's own configuration, and we could easily have 2 ``create-folder`` tasks with different folders to be created.

via ``vars`` key
^^^^^^^^^^^^^^^^

.. code-block:: yaml

   vars:
     path: ~/vars_folder
   tasks:
     - create-folder

Note how the task item is a string, instead of a dictionary in the above example. Also, if we choose this way of providing vars, we can't have a second ``create-folder`` task specified like this, as it would just create the same folder again. We could, however re-use the variable in a different task (e.g. use it as target in a ``get_url`` task).

via ``args``
^^^^^^^^^^^^

.. code-block:: yaml

    args:
      path:
        help: the folder path
        default: ~/cool_folder
    tasks:
      - file:
          state: directory

I'm not using the ``create-folder`` alias here, but the ``file`` Ansible module (which is used by the alias) directly, to show how to provide other sort of variables in addition to the ``args`` key

Conventions
===========

The format of a *frecklecutable* is designed to be as minimal and readable (meaning, it's plain to see what it does) as possible. To achieve this, *frecklecute* relies on a few conventions that somebody looking into writing a *frecklecutable* needs to be aware of.

Specifying the type via the task name
-------------------------------------

For configuration purposes *frecklecute* does not require the user to explicitly state the type of a task, but tries to figure it out by looking at the name itself:

- if the task name is contained in the list of task aliases, it is assumed to be an alias
- if the task contains a '.', it is assumed to be an Ansible role
- if the task contains no '.', it is assumed to either be an Ansible task module

Root/sudo permissions
---------------------

The `become` key, which specifies whether a task should be executed with root/sudo privileges or not, is part of the keys that specify 'meta' properties of a task. This area clearly needs more documentation, but until this is done I'll quickly explain the two ways to tell *frecklecute* to execute a task with elevated privileges:

via the 'meta' dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^

via the task-name case
^^^^^^^^^^^^^^^^^^^^^^

As the `become` key is the most often used one, *frecklecute* allows for a shortcut that doesn't require adding a 'meta' dictionary to a task: if a task name (module or ansible role) is all uppercase, *frecklecute* will convert the string to an all-lowercase one, and add the 'meta' dictionary with a `become: true` key/value pair. E.g.

.. code-block:: console

   tasks:
     - MONGRELION.DOCKER

will become:

.. code-block:: console

   tasks:
     - meta:
         become: true
         task-name: mongrelion.docker

.. note::

   this works for all Ansible modules, as those don't contain uppercase letters in their name. Some Ansible roles contain uppercase letters, even though it's rare. If you want to use one of those you'll have to manually specify the `become` key.

Examples
********

TODO

For now, check out the default executables that ship with *freckles* to get an idea what is possible: https://github.com/makkus/freckles/tree/master/freckles/external/frecklecutables
