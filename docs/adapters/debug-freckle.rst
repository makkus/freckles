==========
debug-freckle
==========

This is a helper adapter to display metadata when developing or debugging a *freckles* adapter.

Usage
-----

.. code-block:: console

   freckles -o verbose debug-freckle [OPTIONS] -f <freckle_url_or_path>

At least one path or url to a freckle needs to be provided (multiple paths can be supplied by simply providing multiple ``--freckle`` options). For this adapter, the default output format doesn't make much sense as it doesn't display debug messages. So we are using the default ansible verbose output.

Options
^^^^^^^

n/a

Metadata
---------

Metadata that can be provided within the *freckle* itself, either via the ``.freckle`` file in the root of the *freckle* directory, or via marker files.


vars
^^^^

n/a

*freckle* folder structure
^^^^^^^^^^^^^^^^^^^^^^^^^^

n/a

Additional files and markers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

n/a


Examples
--------

n/a
