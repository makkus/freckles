# Getting started

## Installing *freckles*

There are several ways to install *freckles*. For the purpose of getting started quickly, we'll use the recommended way, a [bootstrap script](https://gitlab.com/frkl/inaugurate).

Apart from installing the *freckles* package, this script can execute one of the applications that come with it straight away, as well as uninstall the whole she-bang after execution (if so desired). For now we don't have to concern ourselves with any of those more advanced features, all we want to do is get *freckles* on our machine:

```
curl https://freckles.sh/install | bash 
```

or, if we don't have ``curl`` but only ``wget`` available:

```
wget -O- https://freckles.sh/install | bash
```

This will install *freckles* in ``$HOME/.local/share/inaugurate/``, for more details about this process check [here](https://TODO).

To have the *freckles* commands available in your shell session now, we have to source the ``.profile`` file:

```bash
source ~/.profile
```

## Listing available *frecklecutables*

The *freckles* package comes with several command-line applications, the one you'll probably use most in the beginning is called ``frecklecute`` and it lets you execute pre-written task-lists that serve some high-level purpose (typically installing and configuring a service).

Let's get a list of all the task-lists that are supported out of the box:

```
frecklecute --help
{{== __frecklecute_help_text__ ==}}
```

If you want to see all available tasks, not just the high-level ones, you can do:

```bash
frecklecute --help-all
```

## Executing a *frecklecutable*

Once you picked the top-level *frecklecutable* you want to run, you can get it's usage information via:

```bash
frecklecute <frecklecutable_name> --help
```

