---
title: Running frecklets
url_path_prio: 160
draft: false
---

This section explains a few characteristics that are common to running frecklets, independent on the
interface that is used (e.g. ``frecklecute``, ``frecklets``, the Python API, ...).



## Targets {: .section-title}
<div class="section-block" markdown="1">

*freckles* can be used both to setup the local machine (say, your laptop), as well as remote ones, using the exact same command, except for an additional ``target`` argument.

There are a few slight differences when using *freckles* on a local target as opposed to a remote one though, and there are a few different 'remote' connection types that are supported. Please find details about those below.

For the sake of illustration, we'll run the same *frecklet* in a few different ways, on different targets. For this we'll use the fairly simple, but non-trivial [static-website-from-string](https://freckles.io/frecklets/default/web/static-website-from-string) *frecklet*, which will [install an Nginx webserver](https://freckles.io/frecklets/default/service/webserver-service) (if not already present), setup a [Nginx server block to host a static website](https://freckles.io/frecklets/default/web/static-website-from-folder), and then [create a file](https://freckles.io/frecklets/default/filesystem/file-with-content) that contains html to be servced by our webserver.

### *local* target {: .block-title}

*Local* targets are the default, so, for the command-line interfaces (``freckles``, ``frecklecute``), if you don't specify the target argument (``--target``/``-t``) *freckles* assumes you want it to execute its instructions locally. Assuming we have a terminal open on the machine we want to install (either our local machine, a VM or LXD container, or a remote machine we ssh-ed into), we can issue:

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


### *remote* targets {: .block-title}

This is the more interesting use-case, as it allows you to provision one or several remote machines, from the comforts of your home (terminal) shell.

*freckles* supports several remote *'target types'*, 'ssh' being the most common (and default) one.

Targets for a *freckles* run are specified with the ``--target/-t`` command-line argument. In overall syntax for the value of this argument is ``[connection-type][::connection-details]``.

### ssh {: .block-title}

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
$ frecklecute --ask-login-pass -t markus@10.10.10.70 \
     static-website-from-string --content '<h1>Hello World!</h1>'

LOGIN/SSH PASS (for 'markus@10.10.10.70'):

╭╼ starting run
│  ├╼ running frecklet: static-website-from-string (on: 10.10.10.70)
│  │  ├╼ starting Ansible run
...
...
```

This requires the [``sshpass``](https://sourceforge.net/projects/sshpass/) tool to be installed on the machine
that runs *freckles*. You can either do that manually, or follow the instructions in the error message *freckles* displays in case its missing, and use *freckles* itself to install it (``frecklecute sshpass-installed``).

#### ssh-key authentication

This is the default (and recommended) way to access remote machines. The default location for an ssh key
is usually ``$HOME/.ssh/id_rsa`` (the 'rsa' part might differ, depending on the algorithm that was used to create the key). Every ssh key (usually) comes with a public key part (``%HOME/.ssh/id_rsa.pub``). That is used as a sort of 'fingerprint' you can share in a secure way. The content of this key goes into a file called ``$HOME/.ssh/authorized_keys``. The (remote) ssh daemon will check this file, and if one line of this file matches the 'fingerprint' of the key that is used to login, login permission is granted.

If your ssh-key is already setup (on both ends), you don't need to do anything further. If your key is protected by a password, *freckles* will ask for it, create a temporary (for the duration of the execution) ssh-agent, and kill it after the run is finished.

If not, or if you are interested in the details of how all this works, how to create your own ssh key etc, check out the blop post I wrote about it: [A (practical) ssh primer](https://frkl.io/blog/ssh-primer/).

Here's how to do some of the tasks described in that post using *freckles*:

##### Create a ssh-key-pair (with password)

This is the default command to create an ssh-key pair following best practices (4096 bit/ed25519):

```console
$ frecklecute ssh-key-exists  --password ::ask::

Input needed for value 'password': the password to unlock the key (only used if key doesn't exist already)
  password: xxx

╭╼ starting run
│  ├╼ running frecklet: ssh-key-exists (on: localhost)
│  │  ├╼ starting Ansible run
│  │  │  ├╼ create ssh key (if necessary): ~/.ssh/id_ed25519
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok
```

Note the ``::ask::`` string in this command-line invocation. This tells *freckles* to [ask the user for the password](https://freckles.io/doc/security#password-entry). This is more secure than providing the password directly, as, for one, the whole command would show up in the command-line history of this user.

This will have create a private ssh key in ``$HOME/.ssh/id_ed25519``. You can now  put the public key part (content of ``$HOME/.ssh/id_ed25519.pub``) into the ``authorized_keys`` file of a remote server, or give it to services that request it (like GitLab, GitHub, AWS, DigitalOcean...).

##### Create a password-less ssh-key-pair

In some cases it's use-full to have an ssh key that is not protected by a password. Make sure you know what you are doing though, this introduces some security issues. In this example, we are using the 'rsa' algorithm to create the key, and only specify a key length of 2048 bits.

```console
$ frecklecute ssh-key-exists --bits 2048 --key-type rsa
```

###### Add the public key to a remote server

As ssh-key authentication is more secure than password-auth, but in some cases you start off with a remote server that only has a root account and password-auth configured, it's a good idea to create an admin user (with sudo permissions), disable password auth on ssh (as well as ssh access for the root account entirely). *freckles* has a [*frecklet*](https://freckles.io/frecklets/default/security/initial-system-setup) for that, obviously:

<div class="code-max-height" markdown="1">

```console
$ frecklecute --ask-login-pass  -t root@116.203.223.246 \
    initial-system-setup --admin-user admin \
    --admin-pub-key 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJyFmVo2eAUZDeuFLpgTOFQEmd9T+9PeePmsb3005dK9'

LOGIN/SSH PASS (for 'root@116.203.223.246'):

╭╼ starting run
│  ├╼ running frecklet: initial-system-setup (on: 116.203.223.246)
│  │  ├╼ starting Ansible run
│  │  │  ├╼ add admin user: 'admin'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ add authorized_keys for user 'admin'
│  │  │  │  ├╼ ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJyFmVo2eAUZDeuFLpgTOFQEmd9T+9PeePmsb3005dK9
│  │  │  │  │  ╰╼ ok
│  │  │  │  ╰╼ ok
│  │  │  ├╼ enable password-less sudo
│  │  │  │  ╰╼ ok
│  │  │  ├╼ disable password authentication for ssh
│  │  │  ├╼ restart ssh
│  │  │  │  ╰╼ ok
│  │  │  ├╼ disable root access via ssh
│  │  │  │  ╰╼ ok
│  │  │  ├╼ freckfrackery.basic-security : restart ssh
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok

markus@first:~$ ssh admin@116.203.223.246
Enter passphrase for key '/home/markus/.ssh/id_ed25519':
Welcome to Ubuntu 18.04.2 LTS (GNU/Linux 4.15.0-54-generic x86_64)

admin@ubuntu:~$
```

</div>

Here, we provided an admin user name and the public ssh key ('ssh-ed25519 AAAAC...') of the ssh key
to use to login as that user on the remote amchine. The [``initial-system-setup``](https://freckles.io/frecklets/default/security/initial-system-setup) lets us specify some other security-relevant options (which we don't use for this example), like setting up a firewall, or installing 'fail2ban'. We took advantage of some of this *frecklets* default settings though. For example, the new 'admin' user has 'passwordless-sudo' permissions (see below), and password authentication is disabled for the ssh daemon on this machine now.

Note how we had to use the ``--ask-login-pass`` flag. Since only password-auth was available (until now), we could hot have logged in any other way.

If all we wanted to do was add our new ssh key to a users ``authorized_keys`` file, we could have also used the [``ssh-keys-authorized``](https://freckles.io/frecklets/default/system/ssh-keys-authorized) *frecklet*:

<div class="code-max-height" markdown="1">

```console
$ frecklecute --ask-login-pass -t root@116.203.223.246 \
     ssh-keys-authorized --key 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJyFmVo2eAUZDeuFLpgTOFQEmd9T+9PeePmsb3005dK9' \
     -u root

LOGIN/SSH PASS (for 'root@116.203.223.246'):

╭╼ starting run
│  ├╼ running frecklet: ssh-keys-authorized (on: 116.203.223.246)
│  │  ├╼ starting Ansible run
│  │  │  ├╼ updating apt cache
│  │  │  │  ╰╼ ok
│  │  │  ├╼ ensure rsync, ca-certificates and unzip packages are installed
│  │  │  │  ╰╼ ok
│  │  │  ├╼ creating freckles share folder
│  │  │  │  ╰╼ ok
│  │  │  ├╼ creating box basics marker file
│  │  │  │  ╰╼ ok
│  │  │  ├╼ recording python interpreter metadata
│  │  │  │  ╰╼ ok
│  │  │  ├╼ recording box metadata for later runs
│  │  │  │  ╰╼ ok
│  │  │  ├╼ adding authorized_keys
│  │  │  │  ├╼ ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJyFmVo2eAUZDeuFLpgTOFQEmd9T+9PeePmsb3005dK9
│  │  │  │  │  ╰╼ ok
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok

markus@first:~$ ssh root@116.203.223.246
Enter passphrase for key '/home/markus/.ssh/id_ed25519':
Welcome to Ubuntu 18.04.2 LTS (GNU/Linux 4.15.0-54-generic x86_64)

root@ubuntu:~#
```

</div>


</div>

## Elevated permissions {: .section-title}
<div class="section-block" markdown="1">

Most *frecklets* that are bundled with *freckles* contain metadata about whether they need elevated permissions to be executed, or not. Requiring elevated permissions is a common case, for tasks like creating users, installing packages with the system package manager, etc.

In case you are uncertain: 'elevated permission' basically means tasks are (directly) executed by the root user, or (indirectly) via the [sudo](https://kb.iu.edu/d/amyi) command. The latter has to be installed and configured on a host if it is to be used (see below).

### the '--elevated' flag {: .block-title}

If a task/*frecklet* needs elevated permissions, but its metadata doesn't indicate that, your task will fail. You can manually hint to *freckles* to assume elevated permissions are necessary by using the ``--elevated/-e`` command-line flag:

```
frecklecute --elevated <frecklet_name>
```

This flag is not necessary if you log-in as the root user onto a remote host (as you'll automatically have elevated permissions), or if the user you log in as can use *sudo* without having to provide a password.

#### ``sudo`` {: .block-title}

As mentioned earlier, there are two ways you can execute tasks that require elevated permissions: by using/logging in as the root user, or by using the sudo *sudo* command. *freckles* will try to do the later automatically for you, in case tasks requests those permissions.

In provisioning scenarios, it's quite common to setup an admin user that does not need to provide a password when using *sudo* (see ``initial-system-setup`` example above). This is handy, because otherwise it would not be possible running those sorts of tasks in an automated way (as there would always be user-interaction when typing in a password).

In cases where you use *freckles* with a remote target, and a login user that *does* need to provide a password to be able to use *sudo*, you need to add the ``--ask-become-pass`` to your command-line. *freckles* will prompt for the password before the run commences in that case.

By default, if you specify a non-root login user on a remote host, and the *frecklet* you run requires elevated permissions, *freckles* will assume the login user can do passwordless sudo.

</div>
