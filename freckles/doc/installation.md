---
title: Installation
url_path_prio: 2
---

There are a few different ways to bootstrap *freckles*. Depending on the state of your box, your proficiency and your general trust in random people on the internet, you can choose one of the methods below.

## via curl/wget {: .section-title}
<div class="section-block" markdown="1">

The main way of bootstrapping *freckles* is by utilizing [``inaugurate``](https://gitlab.com/frkl/inaugurate), a bash script I wrote for *freckles* but decided to make into it's own project because I figured it might be worth a shot creating a sort of 'generic bootstrap script'.

For how it exactly works, and why you should or should not trust it, head over to it's [homepage](https://gitlab.com/frkl/inaugurate). This method of bootstrapping is the easiest, and fricktionlessest. One of the main reasons for creating *freckles* was that I wanted a way to setup a new box (physical or virtual) by executing only one (easy-ish to remember) line in a terminal. ``inaugurate`` provides that functionality.

``inaugurate`` supports two modes of install: with or without *root*/*sudo* permissions. Although both methods achieve the same result, they go about it a bit differently. Both methods are explained in detail further below.

### 'inaugurate' (without sudo) {: .section-title} 
<div class="section-block" markdown="1">



This is the default way of bootstrapping *freckles*. It will create a self-contained installation (under ``$HOME/.local/share/inaugurate/``), using [conda](https://conda.io/) to install requirements and create its working environment.

#### Commands

Using `curl`:

```
curl https://freckles.sh | bash -s -- frecklecute <args>
```

Using `wget`:

```
wget -O - https://freckles.sh | bash -s -- frecklecute <args>
```

The install process can be influenced with environment variables, more details can be found in the [inaugurate documentation](https://gitlab.com/frkl/inaugurate#environment-variables)

#### What does this do?


This installs the conda package manager ([miniconda](https://conda.io/miniconda.html) actually). Then it creates a [conda environment](https://conda.io/docs/using/envs.html) called 'inaugurate', into which *freckles* along with its dependencies is installed.

Everything that is installed (about 450mb of stuff -- it basically bootstraps its whole execution environment so it doesn't need to depend on anything that might or might not be available locally. In addition to not requiring root, of course) is put into the ``$HOME/.local/share/inaugurate/conda/envs/freckles`` folder, which can be deleted without affecting anything else (except if you installed some other applications using `conda` later on, those might be deleted too).

A line will be added to ``$HOME/.profile`` to add ``$HOME/.local/bin`` to the users ``$PATH`` environment variable.

</div>

### 'inaugurate' (with sudo) {: .section-title} 
<div class="section-block" markdown="1">


This is a quicker (and leaner) way to bootstrap *freckles*, as 'normal' distribution packages are used to install dependencies. The size of the ``$HOME/.local/share/inaugurate`` folder will be smaller, ~70mb -- systems packages are adding to that in other parts of the system though. The *freckles* install itself is done in a *virtualenv* using `pip`. Root permissions are required.

#### Commands

Using `curl`:

```console
curl https://freckles.sh | sudo bash -s -- frecklecute <args>
```

Using `wget`:

```console
wget -O - https://freckles.sh | sudo bash -s -- frecklecute <args>
```

As above, the install process can be influenced with environment variables, more details can be found in the [inaugurate documentation](https://gitlab.com/frkl/inaugurate#environment-variables)

#### What does this do?

This installs all the requirements that are needed to create a Python virtualenv for *freckles*. What exactly those requirements are differs depending on the OS/Distribution that is used (check the 'Install manually via pip' section for details). Then a Python virtual environment is created in ``$HOME/.local/share/inaugurate/virtualenvs/freckles`` into which *freckles* and all its requirements are installed (~70mb).

A line will be added to ``$HOME/.profile`` to add ``$HOME/.local/bin`` to the users ``$PATH`` environment variable.
</div>

### 'inaugurate' options {: .section-title}
<div class="section-block" markdown="1">

In addition to its default way of operating (bootstrapping & running an application), ``inaugurate`` has a few options to make it suitable for different scenarios. For more
detailed information check out it's [README](https://gitlab.com/frkl/inaugurate#environment-variables). Here are a few examples:

#### only install

This will only install the *freckles* package, without running any command.

````console
curl https://freckles.sh | bash
````

#### delete *freckles* after execution

You can delete the whole *freckles* install folder (``$HOME/.local/share/inaugurate``) after running one command. This is useful for when you only want to provision a machine (or container), and don't need freckles around after.

```console
curl https://freckles.sh | SELF_DESTRUCT=true bash -s -- frecklecute pkg-mgr-nix-installed
```

#### don't add to ``PATH``

If you don't want ``inaugurate`` to modify your ``$HOME/.profile`` file, you can do that too.

```console
curl https://freckles.sh | NO_ADD_PATH=true bash -s -- frecklecute admin-user-exists --passwordless-sudo --shell /usr/bin/zsh markus
```

</div>
</div>

## Install manually via 'pip' {: .section-title}
<div class="section-block" markdown="1">

If you prefer to install *freckles* from pypi_ yourself, you'll have to install a few system packages, mostly to be able to install the ``pycrypto`` and ``cryptography`` packages when doing the ``pip install``. 

!!! note
    This section might be outdated information and needs to be reviewed, could be that the ``pycrypto`` and ``cryptography`` packages are available via wheels now...

### Requirements

#### Ubuntu/Debian

```
sudo apt install build-essential git python-dev python-virtualenv libssl-dev libffi-dev
```

#### RedHat/CentOS

```
sudo yum install epel-release wget git python-virtualenv openssl-devel gcc libffi-devel python-devel openssl-devel
```

#### MacOS X

We need Xcode. Either install it from the app store, or do something like:

```bash
touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress;
PROD=$(softwareupdate -l |
       grep "\*.*Command Line" |
       head -n 1 | awk -F"*" '{print $2}' |
       sed -e 's/^ *//' |
       tr -d '\n');
softwareupdate -i "$PROD" -v;
```

We also need to manually install pip:

```
sudo easy_install pip
```

### Install *freckles*

Ideally, you'll install *freckles* into its own virtualenv. But if you read this you'll (hopefully) know how to do that. Here's how to install it system-wide (which I haven't tested, to be honest, so let me know if that doesn't work)

```
sudo pip install --upgrade pip   # just to make sure
sudo pip install freckles
```

We probably also want the [nsbl](https://gitlab.com/freckles-io/freckles-adapter-nsbl) and [shell](https://gitlab.com/freckles-io/freckles-adapter-shell) connectors:

```console
sudo pip install freckles-adapter-nsbl
sudo pip install freckles-adapter-shell
```

Optionally, if necessary (if you didn't do a systemwide install) add *freckles* to your PATH. for example, add something like the following to your ``.profile`` file (obviously, use the location you installed *freckles* into, not the one I show here):

```
if [ -e "$HOME/.virtualenvs/freckles/bin" ]; then export PATH="$HOME/.virtualenvs/freckles/bin:$PATH"; fi
```
</div>
