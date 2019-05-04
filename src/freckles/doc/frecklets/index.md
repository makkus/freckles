---
url_path_prio: 30
title: frecklets
---

*frecklets* are building blocks for the *freckles* framework. Each *frecklet* is
designed to achieve one, fairly narrowly defined, purpose. This can be a small, atomic operation like 'create a directory', or something quite involved, like: 'setup a Wordpress server'.  

At their core, *frecklets* are either list- or dictionary-type data structures, with a sort of ['loose' schema](/doc/frecklets/evolution/#the-elastic-non-schema).

Most commonly, a *frecklet* is a text file in [YAML](http://yaml.org/) format. Other formats like [JSON](https://www.json.org/) or [TOML](https://github.com/toml-lang/toml) are also supported, and, if used within an application, a *frecklet* can be just a list, or a dict in whatever programming language is used.

Here are some resources to find out more about *frecklets*, how they are called, work, and look like:

[Getting started](/doc/getting_started)
:    The recommended guide to get started with using *freckles*. Read this first.

[The evolution of a frecklet](/doc/frecklets/evolution)
:    How to write a *frecklet*. Discusses the different ways a *frecklet* can be implemented, from the most simple and easy, to most feature-full and flexible.

[The anatomy of a frecklet](/doc/frecklets/anatomy)
:    For when you want to create your own, non-trivial *frecklets*. Non essential reading if you just want to use *freckles* to run existing *frecklets*, or cobble together a few simple ones of your own.

[Default frecklet index](frecklets/default)
:    The repository containing the default set of *frecklets* that which is included in the *freckles* application.

[Community frecklet index](/frecklets/community)
:    The repository containing a *frecklets* that were created, improved and maintained by the community.
