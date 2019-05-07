---
title: Installation
url_path_prio: 4
---

DOCUMENTATION STILL TO BE DONE

There are several options for installing *freckles*. The two easiest ones are:

## Binary file download {: .section-title}
<div class="section-block" markdown="1">

The most straightforward way of installing *freckles* is to download the executable of the command you need:

- Linux / [Windows subsystem for Linux](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux) (pure Windows not supported yet)
    - [freckles](https://pkgs.frkl.io/downloads/dev/linux/binaries/freckles)
- Mac OS X
    - [freckles](https://pkgs.frkl.io/downloads/dev/darwin/binaries/freckles)


After download, place the executable somewhere in your path (I usually use ``$HOME/.local/bin`` -- but you might have to add that to your ``$PATH`` environment variable) and make it executable:

```console
mv ~/Downloads/freckles ~/.local/bin
chmod +x ~/.local/bin/freckles
```

 If you intend to also use the ``frecklecute`` application (and you probably want to), also link the file to that name (as the binary contains both the ``freckles`` and ``frecklecute`` applications):

```console
ln -s freckles ~/.local/bin/frecklecute
```

</div>

## [freck](https://gitlab.com/freckles-io/freck), the curly bootstrap script for *freckles* {: .section-title}
<div class="section-block" markdown="1">

A good way of bootstrapping *freckles* on vanilla boxes is by utilizing [``freck``](https://gitlab.com/freckles-io/freck), the official *freckles* bootstrap script.

For how it exactly works, and why you should or should not trust it, head over to it's [homepage](https://gitlab.com/freckles-io/freck). This method of bootstrapping is the easiest, and fricktionlessest. One of the main reasons for creating *freckles* was that I wanted a way to setup a new box (physical or virtual) by executing only one (easy-ish to remember) line in a terminal. ``freck`` provides that functionality.

### Commands

Using `curl`:

```
curl https://freckles.sh | bash
```

Using `wget`:

```
wget -O - https://freckles.sh | bash
```

This will download the approriate binary into ``$HOME/.local/share/freckles/bin``. You can configure the install process with environment variables, more details can be found in the [freck documentation](https://gitlab.com/freckles-io/freck)

### What does this do?

Check out the [``freck`` README file](https://gitlab.com/freckles-io/freck#how-does-this-work-what-does-it-do).

</div>

## Python virtualenv / manual {: .section-title}
<div class="section-block" markdown="1">

TODO

</div>
