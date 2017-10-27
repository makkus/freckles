############
ansible-task
############

This is the most generic frecklecutable, it allows the execution of *one* Ansible module or role.

Usage
*****

.. code-block:: console

   frecklecutable ansible-task [--become] [--vars <json_vars_or_vars_file> --task-name <task_name>

Examples
********

Create a folder using the *file* module
=======================================

.. code-block:: console

   frecklecute ansible-task --task-name file --vars '{"path": "~/cool_folder", "state": "directory"}'

Install *docker* using the *mongrelion.docker* Ansible role
===========================================================

.. code-block:: console

    frecklecute --ask-become-pass true ansible-task --become --task-name mongrelion.docker

.. note::

   Depending on whether the system we run this on supports password-less sudo or not, we also need to add the `--add-become-pass` option. This *frecklecuteable* behaves a bit different to others in this aspect because of it's generic nature.

Code
****

.. literalinclude:: ../../freckles/external/frecklecutables/ansible-task
    :language: yaml
