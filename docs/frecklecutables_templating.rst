############################
*frecklecutables* templating
############################

.. note::

    This is an advanced topic, and the way this works might change in the future

.. note::

    Most of the following assumes you have a basic understanding of yaml, as well as Ansible

Overview
********

``frecklecute`` supports basic templating (similar to Ansible, using Jinja2). There are a few differences in how it works, which are mostly due to technical limitations.

'Allowed' keys
==============

A *frecklecutable* can contain 5 different (top-level) keys: ``doc``, ``defaults``, ``args``, ``vars``, and ``tasks``. To be valid, a *frecklecutable* only needs the ``tasks`` key, and a list of (at least one) tasks as value. We will disregard the ``docs`` key in this context as it's only for documentation/user-help purposes.

To support basic templating, internally ``frecklecute`` divides variables into 2 categories: ``defaults`` and ``vars``.

``defaults``
------------

Not to be confused with *defaults* in Ansible roles, those are mostly used to specify values that are used multiple times in a *frecklecutable*. For example, if you want to create a folder, then download a file into that folder, without templating you'd do something like this:

.. code-block:: yaml

   tasks:
     - file:
         path: /tmp/downloads
         state: directory
     - get_url:
         url: https://raw.githubusercontent.com/makkus/freckles/master/README.rst
         dest: /tmp/downloads/

Using templating, you can 'extract' the *path* variable and put it somewhere separate, so you can easily change it later for example:

.. code-block:: yaml

   defaults:
     path: /tmp/downloads
   tasks:
     - file:
         dest: "{{ path }}"
         state: directory
     - get_url:
         dest: "{{ path }}"
         url: https://raw.githubusercontent.com/makkus/freckles/master/README.rst

Values from the ``defaults`` key will never directly end up as a task item value. They always have to be used as a 'replacement' value under either the ``vars`` or ``tasks`` key.

``vars``
--------

Contrary to ``defaults``, a key/value pair under ``vars`` *always* ends up in a task item because ``frecklecute`` adds it to every list item under the ``tasks`` key. You can't, however use the variable to do template substitution (in neither subsequent ``vars`` nor ``tasks`` items).

An example:

.. code-block:: yaml

   vars:
      dest: /tmp/
   tasks:
      - get_url:
           url: https://raw.githubusercontent.com/makkus/freckles/master/README.rst
      - get_url:
           url: https://raw.githubusercontent.com/makkus/freckles/master/HISTORY.rst

This would be the same as writing:

.. code-block:: yaml

   tasks:
      - get_url:
           dest: /tmp/
           url: https://raw.githubusercontent.com/makkus/freckles/master/README.rst
      - get_url:
           dest: /tmp/
           url: https://raw.githubusercontent.com/makkus/freckles/master/HISTORY.rst


This is generally not as useful as using ``defaults``, as most of the time you want finer-grained control. Also, this adds the additional complication that *Ansible modules* behave differently than *Ansible roles* when a non-supported variable is added to it's task description in an *Ansible playbook*: *roles* just ignore them, *modules* error out. By default, *frecklecute* does not know which variable keys are supported by a *module*, so in a case where you want to use ``vars``, but your task list includes an Ansible module that doesn't support one of the ``vars`` keys in your frecklecutable, you have to provide it with a list of 'valid' keys. For example, this would fail:

.. code-block:: yaml

   vars:
     dest: /tmp/downloads
   tasks:
     - file:
         state: directory
     - get_url:
         url: https://raw.githubusercontent.com/makkus/freckles/master/README.rst
     - shell:
         free_form: cat /tmp/downloads/README.rst >> /tmp/some_file


.. note::

    Remember, we can't do ``cat "{{ dest }}/README.rst" >> /tmp/some_file`` because ``vars`` can't be used as templating variables themselves.

Both the ``file`` as well as the ``get_url`` task items are Ansible modules and support the ``dest`` key (in the case of ``file``, ``dest`` is an alias for ``path``). The ``shell`` module, however, doesn't support ``dest``, which will lead to an error message:

.. code-block:: console

   $ frecklecute test.yml

    * starting tasks (on 'localhost')...
     * starting custom tasks:
         * file... ok (no change)
         * get_url... ok (no change)
         * debug... failed: 'dest' is not a valid option in debug
       =>
    failed: 'dest' is not a valid option in debug

One way to resolve this would be to use ``defaults``:

.. code-block:: yaml

    defaults:
      path: /tmp/downloads
    tasks:
      - file:
          dest: "{{ path }}"
          state: directory
      - get_url:
          dest: "{{ path }}"
          url: https://raw.githubusercontent.com/makkus/freckles/master/README.rst
      - shell:
          free_form: "cat {{ path }}/README.rst >> /tmp/some_file"

Another way would be to 'tell' `frecklecute` which vars to forward to a task item. This is only possible in the 'exploded` form of a task item (check :doc:`Writing frecklecutables </writing_frecklecutables>` for details on that):

.. code-block:: yaml

    vars:
       dest: /tmp/downloads
    tasks:
       - file:
           state: directory
       - get_url:
           url: https://raw.githubusercontent.com/makkus/freckles/master/README.rst
       - meta:
           name: shell
           var-keys:
             - free_form
         vars:
           free_form: cat /tmp/downloads/README.rst >> /tmp/some_file

Even thoughh key/value pairs from ``vars`` can't be used as substitution 'sources' they can themselves be 'targets' for variables from ``defaults``. To continue the example from above, we could do something like this:

.. code-block:: yaml

    defaults:
        path: /tmp/downloads
    vars:
        dest: "{{ path }}"
    tasks:
        - file:
            state: directory
        - get_url:
            url: https://raw.githubusercontent.com/makkus/freckles/master/README.rst
        - meta:
            name: shell
            var-keys:
               - free_form
          vars:
            free_form: "cat {{ path }}/README.rst >> /tmp/some_file"


``args``
--------

``args`` are a special case. They are used to ask a user for values for variables, and they can be either of type ``defaults`` or ``vars``. To tell ``frecklecute`` which it is in every case, you have to add the ``is_var`` key (which defaults to ``true``):

.. code-block:: yaml

   args:
      path:
        help: the download path
        is_var: false
   vars:
        dest: "{{ path }}"
   tasks:
        - file:
            state: directory
        - get_url:
            url: https://raw.githubusercontent.com/makkus/freckles/master/README.rst
        - meta:
            name: shell
            var-keys:
               - free_form
          vars:
            free_form: "cat {{ path }}/README.rst >> /tmp/some_file"

This is how we'd execute this:

.. code-block:: console

    $ frecklecute test.yml --path /tmp/downloads/

    * starting tasks (on 'localhost')...
     * starting custom tasks:
         * file... ok (changed)
         * get_url... ok (changed)
         * running shell command... ok (changed)
       => ok (changed)
