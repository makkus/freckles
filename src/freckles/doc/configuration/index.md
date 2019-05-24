---
title: Configuration / contexts
url_path_prio: 10
---

### Contexts {: .section-title}
<div class="section-block" markdown="1">

Each freckles run happens in a so-called 'context'. A 'context' is a set of configuration values that determine where
*frecklets* and other resources are allowed to come from, which *frecklets* are available to run, and how the execution of those *frecklets* happens.

For details about context, please check [here](/doc/configuration/contexts)

</div>

### Settings {: .section-title}
<div class="section-block" markdown="1">

*freckles* has a fairly large amount of configuration options, esp. if you consider that every adapter can come with their own additional set. Not that there are many adapters yet, but still. *freckles* comes with an auto-documenting & -validating configuration sub-system (check out the ``freckles context --help`` sub-command to get an idea).

For a list of the most important settings, check [here](/doc/configuration/settings)

</div>

### Repositories {: .section-title}
<div class="section-block" markdown="1">

One of the most important setting is the ``repos`` configuration option. *frecklets* as well as *resources* either come included with the *freckles* package, one of the packages that contain a *freckles* connector, or they can be imported into a *freckles* run from a local folder or a remote git repository.

For more details how repositories work, check [here](/doc/configuration/repositories)

</div>
