=============
debug-freckle
=============

This is a helper adapter to display metadata when developing or debugging a *freckles* adapter.

.. note::

   Within the *freckelize* adapters this one is treated as a special case, which means it can't be used in runs with multiple adapters. In contrast to 'normal' adapters who only see metadata that is either under the general ``freckle`` key, or the key that is the name of the profile itself, this adapter can see all vars under all (primary) keys in a ``.freckle`` metadata file. So, if you have a freckle that uses multiple of those keys you might get misleading results using this adapter. As this is mainly used for developing new adapters I think that's an acceptable tradeoff, but one has to be aware of this pitfall.


Usage
-----

.. code-block:: console

   freckelize -o skippy --ask-become-pass false debug-freckle [OPTIONS] -f <freckle_url_or_path>

At least one path or url to a freckle needs to be provided (multiple paths can be supplied by simply providing multiple ``--freckle`` options). For this adapter, the default output format doesn't make much sense as it doesn't display debug messages. So we are using the ansible 'skippy' callback instead.

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
