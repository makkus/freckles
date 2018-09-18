frecklets
---------

*frecklets* are the basic building block of the *freckles* framework. Each *frecklet*, as a minimum, contains a task list with at least one task. In addition, it can contain metadata about itself, for example documentation, or what arguments it can be called with.

Each of the items in the tasklist of a *frecklet* can either reference another *frecklet*, or an atomic task that is executed by any of the supported `connector <freckles_connectors>`_ plugins.

To get an idea, here's a frecklet (let's save it in a file called ``create-user.frecklet``)

.. toctree::
   :maxdepth: 2

   frecklet/frecklet_evolution
   frecklet/frecklet_anatomy
