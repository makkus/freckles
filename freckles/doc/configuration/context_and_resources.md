---
title: Context & resources
---

# Context, resources, and repositories

## Context

Each freckles run happens in a so-called 'context'. A 'context' contains a list of available *frecklets* (indexed by their name), and external resources that might be needed for those *frecklets*.

## Resources

Depending on the *frecklet* type (and the [connector](/documentation/connectors) that is used to provide that type, resources can be anything from an [Ansible role](docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html) to executalbes, to [shell functions](www.shellscript.sh/functions.html).

## Repositories

*frecklets* as well as *resources* either come included with the *freckles* package, one of the packages that contain a *freckles* connector, or they can be imported into a *freckles* run from a local folder or a remote git repository.
