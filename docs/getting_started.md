# Getting started

## Installing *freckles*

There are several ways to install *freckles*. For the purpose of getting started quickly, we'll use a [bootstrap script](https://gitlab.com/frkl/inaugurate) that was developed specifically for *freckles*.

Apart from installing the *freckles* package, this script can execute one of the applications that come with it straight away, as well as uninstall the whole she-bang after execution (if so desired). For now we don't have to concern ourselves with any of those more advanced features, all we want to do is get *freckles* on our machine:

```
curl https://install.freckles.sh
```

or, if we don't have ``curl`` but only ``wget`` available:

```
wget -O- https://install.freckles.sh
```

This will install *freckles* under ``$HOME/.local/share/inaugurate/``, for more details about this process check [here](https://TODO).


## Listing available *frecklecutables*

The *freckles* package comes with several command-line applications, the one you'll probably use most in the beginning is called ``frecklecute`` and it lets you execute pre-written task-lists that serve some high-level purpose (typically installing and configuring a service).

Let's get a list of all the task-lists that are supported out of the box:

```
$ frecklecute --help
{{== __frecklecute_help_text__ ==}}
```
