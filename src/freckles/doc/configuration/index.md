---
title: Configuration / contexts
url_path_prio: 10
draft: false
---

DOCUMENTATION STILL TO BE DONE - CHECK BACK LATER

### Context {: .section-title}
<div class="section-block" markdown="1">

Each freckles run happens in a so-called 'context'. A 'context' contains a list of available *frecklets* (indexed by their name), and external resources that might be needed for those *frecklets*.
</div>
### Resources {: .section-title}
<div class="section-block" markdown="1">

Depending on the *frecklet* type (and the [adapter](/doc/adapters) that is used to provide that type, resources can be anything from an [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html) to executables, to [shell functions](https://www.shellscript.sh/functions.html).

</div>
### Repositories {: .section-title}
<div class="section-block" markdown="1">

*frecklets* as well as *resources* either come included with the *freckles* package, one of the packages that contain a *freckles* connector, or they can be imported into a *freckles* run from a local folder or a remote git repository.

</div>
