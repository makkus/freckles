#############
ansible-tasks
#############

The `ansible-tasks` adapter is a quite powerful one, as it can execute arbitrary Ansible modules using task lists that are located in the *freckle* folder. This means, if you use this adapter you should be sure you trust the *freckle* is either created by yourself, or somebody you trust.

This adapter can't execute Ansible roles, as those are not present when the `freckelize` run is started. I might add an option that allows for manual addition of dependency roles later on, but only if I come across use-cases that make a lot of sense.

Usage
*****

.. code-block:: console

   freckelize ansible-tasks [OPTIONS] -f <freckle_url_or_path>

At least one path or url to a freckle needs to be provided (multiple paths can be supplied by simply providing multiple ``--freckle`` options)

Options
=======

``--freckle``
    the path or url that points to a 'python-dev' freckle

Metadata
========

Metadata that can be provided within the *freckle* itself, either via the ``.freckle`` file in the root of the *freckle* directory, or via marker files.

By default

vars
----

``task_list``
    a list of files containing ansible tasks to execute (defaults to `[.tasks.freckle]` in the root of the *freckle* folder)


*freckle* folder structure
--------------------------

.. code-block:: console

   <freckle_root>
           ├── .freckle (optional)
           ├── .tasks.freckle (optional)
           ├── <task_file_1> (optional)
           ├── <task_file_2> (optional)
           .
           .                        ...
           .                        ...

Additional files and markers
----------------------------

If the `task_list` variable is empty, this adapter looks for a file called `.tasks.freckle` in the root of the *freckle* folder. If that exists, it executes the tasks contained in it.

If the `task_list` variable is defined and non-empty, the filenames (using the relative path from the *freckle* folder) is interpreted as a file containing a task list to be executed. A potentially existing `.tasks.freckle` file is ignored in this case.


Example ``.freckle`` files
--------------------------

Simple default task_list file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   ansible_tasks:
      task_lists:
        - task_list_1
        - task_list_2
        - ...

Example file `task_list_`:

.. code-block:: yaml
   - name: 'creating folders in home dir'
     file:
       path: "{{ item }}"
       state: directory
     with_items:
       - "~/.backups/zile"
       - "~/.cache"


