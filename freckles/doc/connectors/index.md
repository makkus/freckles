nav_priority: 1000
title: Connectors
draft: true

# Overview

*freckles* itself is only a framework to assemble lists of tasks. In order to actually *do* anything, it relies on plugins -- so called *connectors*.

*Connectors* are basically wrappers around languages or frameworks, and they abstract those languages' instructions and augment them with metadata, so *freckles* can use them as atomic 'task' building blocks.

## Included *connectors*

### [nsbl](https://gitlab.com/freckles-io/freckles-connector-nsbl)

A connector that can use [Ansible](https://ansible.com) [modules](docs.ansible.com/ansible/latest/modules/list_of_all_modules.html), [roles](https://galaxy.ansible.com) and [tasklists](docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_includes.html#including-and-importing-task-files).

### [shell](https://gitlab.com/freckles-io/freckles-connector-shell)

A connector that provides a few different ways to assemble shell-scripts.
