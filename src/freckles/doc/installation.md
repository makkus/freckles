---
title: Installation & update
url_path_prio: 4
---

There are several options for installing *freckles*. The two easiest ones are:

## Installation {: .section-title}
<div class="section-block" markdown="1">

### Binary file download {: .block-title}
<div class="section-block" markdown="1">

The most straightforward way of installing *freckles* is to download the executable of the command you need:

- Linux / [Windows subsystem for Linux](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux) (pure Windows not supported yet)
    - [freckles](https://dl.frkl.io/linux-gnu/freckles)
- Mac OS X
    - [freckles](https://dl.frkl.io/darwin/freckles)


After download, place the executable somewhere in your path (I usually use ``$HOME/.local/bin`` -- but you might have to add that to your ``$PATH`` environment variable) and make it executable:

```
mv ~/Downloads/freckles ~/.local/bin
chmod +x ~/.local/bin/freckles
```

 If you intend to also use the ``frecklecute`` application (and you probably want to), also link the file to that name (as the binary contains both the ``freckles`` and ``frecklecute`` applications):

```
ln -s freckles ~/.local/bin/frecklecute
```

</div>

### Bootstrap script {: .block-title}
<div class="section-block" markdown="1">

A good way of bootstrapping *freckles* on vanilla boxes is by utilizing [``freck``](https://gitlab.com/freckles-io/freck), the official *freckles* bootstrap script.

For how it exactly works, and why you should or should not trust it, head over to it's [homepage](https://gitlab.com/freckles-io/freck). This method of bootstrapping is the easiest, and fricktionlessest. One of the main reasons for creating *freckles* was that I wanted a way to setup a new box (physical or virtual) by executing only one (easy-ish to remember) line in a terminal. ``freck`` provides that functionality.

#### Commands

Using `curl`:

```
curl https://freckles.sh | bash
```

Using `wget`:

```
wget -O - https://freckles.sh | bash
```

This will download the appropriate binary into ``$HOME/.local/share/freckles/bin``. You can configure the install process with environment variables, more details can be found in the [freck documentation](https://gitlab.com/freckles-io/freck).

If you have security concerns using this, please visit the [security section](/doc/security#the-bootstrap-script).

#### What does this do?

Check out the [``freck`` README file](https://gitlab.com/freckles-io/freck#how-does-this-work-what-does-it-do).

</div>

### Python virtualenv {: .block-title}
<div class="section-block" markdown="1">

There will be more details on this later, for now, just quickly:

```console
# for python >= 3.4
python -m venv ~/.virtualenvs/freckles
source . ~/.virtualenvs/freckles/bin/activate
pip install freckles-cli

freckles --help
```

</div>

</div>

## Update {: .section-title}
<div class="section-block" markdown="1">

### Manual {: .block-title}
<div class="section-block" markdown="1">

Just re-download the file you downloaded earlier, and replace the older binary. That's all.

### Bootstrap script {: .block-title}

If you have used the bootstrap script to install *freckles*, you can also use it for updating. Just add the ``UPDATE=true`` environment variable:


Using `curl`:

```
curl https://freckles.sh | UPDATE=true bash
```

Using `wget`:

```
wget -O - https://freckles.sh | UPDATE=true bash
```

</div>
</div>
