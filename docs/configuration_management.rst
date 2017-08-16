If you are familiar with ansible_, puppet_, chef_, or saltstack_, you know about configuration management, and why it (mostly) is a good idea. If not: in short, configuration management gives you a way to describe a machine/server and the services and applications it runs. Either in code, or a configuration format like json or yaml. Then it takes that configuration and applies it to a machine, removing the need for you to setup the machine maunually, as well as guaranteeing that the machine is always setup the same way, even after a re-install.

Because of the overhead that come with configuration management systems, using them is usually restricted to situations where the infrastructure to be controlled is deemed to cross a certain threshold of... let's call it 'importance'. While for production services, or other business-relevant systems this threshold is often crossed even for single servers, this is not usually the case for the physical (or virtual) machines developers (or somesuch) use when going about whatever they go about. There are exceptions of course, but spending the time to learn about, and then setting up a system like that is not always worth it. *freckles* tries to change that equation by making it easier, and faster, to apply the principles of configuration management to local development environments. I do think there's a lot of developers time to be saved, to be used on actual development, rather than all the annoying stuff around it...


.. _puppet: https://puppet.com
.. _chef: https://www.chef.io/chef
.. _saltstack: https://saltstack.com
