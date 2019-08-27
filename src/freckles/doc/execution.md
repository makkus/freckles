---
title: Executing 'frecklets'
url_path_prio: 160
draft: false
---

This section explains a few characteristics that are common to running frecklets, independent on the
interface that is used (e.g. ``frecklecute``, ``frecklets``, the Python API, ...).



## Targets {: .section-title}
<div class="section-block" markdown="1">

*freckles* can be used both to setup the local machine (say, your laptop), as well as remote ones, using the exact same command, except for an additional ``target`` argument.

There are a few slight differences when using *freckles* on a local target as opposed to a remote one though, and there are a few different 'remote' connection types that are supported. Please find details about those below.

So, for the sake of illustration, we'll run the same *frecklet* in a few different ways, on different targets. For this we'll use the fairly simple, but non-trivial [static-website-from-string](https://freckles.io/frecklets/default/web/static-website-from-string) *frecklet*, which will [install an Nginx webserver](https://freckles.io/frecklets/default/service/webserver-service) (if not already present), setup a [Nginx server block to host a static website](https://freckles.io/frecklets/default/web/static-website-from-folder), and then [create a file](https://freckles.io/frecklets/default/filesystem/file-with-content) that contains html to be servced by our webserver.

### *local* target {: .block-title}

*Local* targets are the default, so, for the command-line interfaces (``freckles``, ``frecklecute``), if you don't specify the target argument (``--target``/``-t``) *freckles* assumes you want it to execute its instructions locally. So, assuming we have a terminal open on the machine we want to install (either our local machine, a VM or LXD container, or a remote machine we ssh-ed into), we can issue:

```console
$ frecklecute static-website-from-string --content '<h1>Hello World!</h1>'

SUDO PASS (for 'localhost'):
╭╼ starting run
│  ├╼ running frecklet: static-website-from-string (on: localhost)
│  │  ├╼ starting Ansible run
...
...
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok

$ curl http://127.0.0.1
<h1>Hello World!</h1>
```

As you can see, *freckles* asked for the 'sudo' password. Since it is executed on the same host it wants to
provision, it can easily check whether a) the task requires elevated permissions, and b) it can get those elevated permissions without having to ask for a password (see the 'Elevated permissions' section below for more details).


### *remote* targets {: .section-title}

This is the more interesting use-case, as it allows you to provision one or several remote machines, from the comforts of your home (terminal) shell.

*freckles* supports several remote *'target types'*, 'ssh' being the most common (and default) one.

Targets for a *freckles* run are specified with the ``--target/-t`` command-line argument. In overall syntax for the value of this argument is ``[connection-type][::connection-details]``.

### ssh

[ssh](https://searchsecurity.techtarget.com/definition/Secure-Shell) is a network protocol that lets you access remote hosts that have an ssh server daemon installed. Authentication depends on how the remote daemon is configured, but 2 common options are 'username/password', and 'ssh-key' authentication. It is strongly recommended to setup 'ssh-key' authentication for your remote server, as it is considered more secure.

Depending on the supported authentication methods on the remote server, you might have to adjust your connection-related command-line arguments.

But let's have a look first how to connect to a remote server via *ssh* in general:

As *ssh* is the default connection-type, you can omit the '``connection-type``' part of the string (as a matter of fact, you actually have to, ``ssh::...`` isn't supported at the moment).

Here's an example how to connect to the 'admin' user on the 'dev.frkl.io' host:

```console
$ frecklecute -t admin@frkl.dev.io static-website-from-string \
     --content '<h1>Hello World!</h1>'
```

We can also specify an ip address instead of a domain name, and change the user to be 'root' instead at the same time:

```console
$ freckles -t root@10.10.10.70 static-website-from-string \
     --content '<h1>Hello World!</h1>'
```

In case we the remote username is the same as our local one, we can omit the 'user' part entirely:

```console
$ frecklecute -t other.example.com static-website-from-string \
     --content '<h1>Hello World!</h1>'
```

#### username/password auth

In case you want to provision a server that only supports username/password authentication with *freckles*, you can do that via the '--ask-login-pass' command-line flag. This flag instructs *freckles* to ask you for the password:

```console
$ frecklecute -c freckles-dev --ask-login-pass -t markus@10.10.10.70 \
     static-website-from-string --content '<h1>Hello World!</h1>'

LOGIN/SSH PASS (for 'markus@10.10.10.70'):

╭╼ starting run
│  ├╼ running frecklet: static-website-from-string (on: 10.10.10.70)
│  │  ├╼ starting Ansible run
...
...
```

This requires the [``sshpass``](https://sourceforge.net/projects/sshpass/) tool to be installed on the machine
that runs *freckles*. You can either do that manually, or follow the instructions in the error message *freckles* displays and use *freckles* itself for it (``frecklecute sshpass-installed``).

#### ssh-key authentication

</div>

## Elevated permissions {: .section-title}
<div class="section-block" markdown="1">

Most *frecklets* that are bundled with *freckles* contain metadata about whether they need elevated permissions
to be executed. 'Elevated permission' basically means they are (directly) executed by the root user, or (indirectly) via the [sudo](https://kb.iu.edu/d/amyi) command. The latter has to be installed and configured on a host if it is to be used (see below).

### the '--elevated' flag

If a task needs elevated permissions, but its metadata doesn't indicate that, your task will fail. You can manually hint to *freckles* to assume elevated permissions are necessary by using the ``--elevated/-e`` command-line flag:

```
frecklecute --elevated <frecklet_name>
```

#### ``sudo``

</div>
