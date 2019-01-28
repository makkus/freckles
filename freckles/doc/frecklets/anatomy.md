---
title: The anatomy of a frecklet
url_path_prio: 2000
---

## example: creating a user

To understand the anatomy of a *frecklet*, let's have a look at a full-blown one that is actually used (and [included](https://gitlab.com/freckles-io/frecklets-nsbl/blob/develop/system/users/create-user.frecklet) in the frecklet package). This one let's you ensures that user exists on a host machine (as well as their optional group). It also gives the option to specify the UID and whether the user is supposed to be a system user or not:

```yaml
{{== __ensure_user_frecklet_string__ ==}}
```

This is what *freckletcute* tells us about it:

```
$ frecklecute create-user --help
Usage: frecklecute create-user [OPTIONS] USER_NAME

  ensures a user exists on a system

Options:
  --gid GID           the gid of the optional group
  --group GROUP_NAME  the name of the users main group
  --system            whether this user should be created as
                      system user  [default: False]
  --uid UID           the uid of the user
  --help              Show this message and exit.
```

Let's have a look at the sections this file:

### documentation: ``doc``

The ``doc`` section houses the general documentation about a *frecklet*. What it does, how it does it (if applicable). This section is optional, but it is highly recommended to have one in a *frecklet*, esp. if you plan to share it with other people. But also as record for yourself in 6 months...

``` yaml
{{== __ensure_user_doc_string__ ==}}
```

The main two keys of this section are called ``help`` and ``short_help``. The ``short_help`` value string is used as text to display
for example when calling ``frecklecute --help``. The ``help`` value is a string in markdown format, and it's used when calling ``--help`` on the specific *frecklet* (see example above).

Note the format of the ``help`` key:

``` yaml
help: |
  Ensure a ...

  Optionally ..
```

This is using the YAML [multiline](https://til.hashrocket.com/posts/d7c96e2ee7-multiline-strings-in-yaml) block format,
if you are familiar with YAML you can also use other supported ways of specifying multi-line strings.

### documentation: ``args``

This

``` yaml
{{== __ensure_user_args_string__ ==}}
```

### documentation: ``frecklets``

``` yaml
{{== __ensure_user_tasks_string__ ==}}
```

## full schema

Here's the basic schema for *frecklets*:

```yaml
{{== __frecklet_schema_string__  ==}}
```

Under the hood, *freckles* is using the brilliant [Cerberus](http://docs.python-cerberus.org/en/stable/) library. Check out its documentation whenever you come across a schema in *freckles*.
