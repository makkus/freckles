nav_priority: 3
title: frecklets

*frecklets* are basically [elastic configuration](https://frkl.io/blog/to_write) files. They configure a list of tasks, in an as minimal way as possible. Or, conversely, as elaborately as necessary.

*frecklets* are text files in the [YAML](http://yaml.org/) format. Other formats like [JSON](https://www.json.org/) or [TOML](https://github.com/toml-lang/toml) might be supported in the future.

If the base element of a *frecklet* is a list, it is interpreted as a list of tasks, without any metadata (documentation, argument descriptions, etc.). This allows for a quick way to put together utility scripts, but it is not recommended for anything you plan to re-use in the future, and possibly build upon. 

If it is a dictionary/map, it needs to contain the ``tasks`` key, otherwise it is considered invalid. Other (optional) allowed keys are: ``doc``, ``args``, ``meta``. For more information on how that works, please check out the '[evolution of a frecklet](/doc/frecklets/evolution)' and '[anatomy of a frecklet](/doc/frecklets/anatomy) pages.
