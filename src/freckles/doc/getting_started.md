---
url_path_prio: 1
title: Getting started
---

## Installing *freckles* {: .section-title}
<div class="section-block" markdown="1">

There are several ways to get *freckles* installed. The easiest one is to use the [*freckles* bootstrap script](https://gitlab.com/freckles-io/freck):

```console
curl https://freckles.sh | bash
source ~/.profile
```

For details what exactly the bootstrap script does, and for other options to get *freckles* onto your machine, please check out the [Downloads page](/downloads) and the [install documentation](/doc/installation).

</div>

<!-- getting help -->
## Getting help {: .section-title}
<div class="section-block" markdown="1">

*freckles* operates on lists of tasks, each such list of tasks is called a *frecklet*. A *frecklet* contains one or more task items, of which each one can either be a low-level, atomic operation (e.g. 'create a directory'), or another *frecklet* (which typically encapsulates a higher-level objective, like for example 'setup a Wordpress instance'). You will be dealing mostly with the former, at least initially.

The *freckles* package comes with several commandline applications, the one you'll probably use most in the beginning is called ``frecklecute`` and it lets you execute one out of a set of *frecklets* that are shipped with *freckles* by default, as well as your own, local ones. A typical purpose would be installing and configuring a service, or setting up the environment for a development project.

To display help for ``frecklecute`` (as well as any of the other included applications), use the ``--help`` flag:

<div class="code-max-height" markdown="1">

```console
> frecklecute --help

Usage: frecklecute [OPTIONS] FRECKLET [ARGS]

  Execute frecklets using an auto-generated command-line interface.

  frecklecute supports executing any frecklet that is available in the
  current context as well as external ones. If the selected FRECKLET option
  is a file and exists, it will be parsed, validated, and executed. If not,
  a context-lookup will be performed and, if found, that frecklet will be
  used.

  In case no frecklet is found with the provided command, that command is
  interpreted as frecklet content in either 'yaml', 'json', or 'toml' format
  and frecklecute will attempt to parse and run this.

  Use the '--list' option to get a list of all available frecklets in the
  current context, or '--apropos <search_term>' for a filtered list.

Options:
  --community           use resources from the freckles community repo
  -r, --repo TEXT       additional repo(s) to use
  -c, --context TEXT    select context/config profile(s)
  --no-run              create the run environment (if applicable), but don't
                        run the frecklet
  --ask-sudo-pass       ask for the sudo password
  --ask-ssh-pass        ask for the connection password
  -e, --elevated        indicate that this run needs elevated permissions
  -ne, --not-elevated   indicate that this run doesn't need elevated
                        permissions
  -v, --vars VARS_TYPE  additional vars, higher priority than frecklet vars,
                        lower priority than potential user input
  -t, --target TEXT     the (default) target to use
  --version             the version of freckles you are using
  --describe            Only describe tasks for this run, don't create an
                        environment and run the frecklet.
  --verbosity LVL       Either CRITICAL, ERROR, WARNING, INFO or DEBUG
  -a, --apropos WORD    Show this message, listing all commands that contain
                        this value in their name or description.
  -l, --list            Show this message, listing all available frecklets.
  -h, --help            Show this message

  frecklecute is part of the 'freckles' project. It is free to use in
  combination with open source software. For more information on licensing
  and documentation please visit: https://freckles.io
```
</div>
<!-- getting help -->

<!-- list available frecklets -->
### List available *frecklets* {: .block-title}

<div class="section-block" markdown="1">

Let's get a list of all the *frecklets* that are supported out of the box, use the ``--list`` flag (this might take a few moments, as it needs to process the current context):

<div class="code-max-height" markdown="1">

```console
> freckles list  

frecklet                             description
-----------------------------------  ----------------------------------------
admin-user-exists                   ensure an admin user with elevated
                                    permissions exists
ansible-module                      execute a specific Ansible module
ansible-role                        execute an arbitrary role from Ansible
                                    Galaxy
apache-vhost-from-folder            configure an Apache vhost for static
                                    site
archive-extracted                   extracts an archive
basic-hardening                     basic security set-up for a newly
                                    installed server
command-output-to-file              execute a command, write the output to
                                    file
config-value-in-file                adds a key/value pair to a file
config-values-in-file               adds key/value pairs to a file
debug-msg                           display a debug message
debug-var                           displays the content of an (internal)
                                    Ansible variable
debug-vars                          displays the content of an (internal)
                                    Ansible variable
devpi-create-backup                 backs-up a devpi service
devpi-import-from-backup            restores up a devpi service backup
devpi-nginx-vhost-config            creates a vhost for devpi on Nginx
devpi-service                       installs a complete devpi server,
                                    including nginx proxy & lets-encrypt
                                    certs
devpi-standalone                    installs a complete devpi server,
                                    including nginx proxy & lets-encrypt
                                    certs
docker-service                      makes sure Docker is installed
dotfiles                            setup dotfiles and associated apps
execute-ad-hoc-script               create an executable file from a
                                    template, execute it, delete it
execute-command                     execute a one-off command
execute-shell                       execute a one-off shell command
file-downloaded                     download a file
file-fetched                        fetches a file from a remote (target)
                                    host
file-is-present                     ensure a file exists
file-with-content                   ensure a file exists and has a certain
                                    content
folder-exists                       ensure a folder exists
folder-is-empty                     ensure a folder exists
folder-stowed                       stow (symlink) a folder
folders-intermingled                merge a target folder with another
frecklecute                         execute a frecklet indirectly
git-repo-synced                     check out or pulls a git repo
gitlab-deploy-key-present           add a deploy key to a Gitlab server
grafana-service                     installs the grafana service
group-exists                        ensure a group exists
hostname                            set the hosts hostname
inaugurate-custom-script            generate a custom inaugurate script
init-service-configured             configure an init service
init-service-disabled               disable init-service
init-service-enabled                enable init-service
init-service-reloaded               reload init service
init-service-restarted              restart init-service
init-service-started                start init-service
init-service-stopped                stop init-service
initial-system-setup                basic security setup for a new server,
                                    incl. setup of admin user."
ipv4-address-assigned               make sure an IPv4 address is assigned to
                                    an interface
lang-go                             make sure Go is available
lang-java                           install OpenJDK if not already available
lang-php                            make sure PHP is installed
lang-python                         install a Python runtime for a user
letsencrypt-cert-exists             ensures a letsencrypt https certificate
                                    for a hostname exists
link-exists                         ensure a filesystem link exists
locales-generated                   ensure a set of locales is generated on
                                    a system
mariadb-database-exists             installs MariaDB (if necessary), and
                                    makes sure a specified database exists
mariadb-service                     ensures MariaDB service is installed
matomo-standalone                   install Matomo analytics service
netdata-service                     makes sure netdata service is installed
                                    and running
nginx-inaugurate-vhost              creates a vhost to host a 'inaugurate'
                                    bootstrap script
nginx-reverse-proxy-vhost-config    n/a
nginx-vhost-from-folder             configure a Nginx vhost for static site
package-installed                   install a single packages
package-managers                    install one or several package managers
packages-installed                  install a list of packages
parent-folder-exists                ensure the parent folder of a path
                                    exists
passwordless-sudo-users             grant passwordless sudo permission to a
                                    user
path-archived                       archives a file or folder
path-attributes                     makes sure a file/folder has a certain
                                    owner/group
path-has-mode                       make sure a file/folder has a certain
                                    mode
path-is-absent                      ensure a file or folder is absent
path-is-owned-by                    make sure a file/folder has a certain
                                    owner/group
path-is-synced                      make sure a file or folder is synced
                                    between two locations
pip-requirements-present            install dependencies so 'pip' can be
                                    used by Ansible
pkg_mgr-asdf                        ensures 'asdf' is installed
pkg_mgr-asdf-plugin                 install a plugin for asdf
pkg_mgr-conda                       install the 'conda' package manager
pkg_mgr-homebrew                    ensure the 'homebrew' package manager is
                                    installed
pkg_mgr-nix                         ensure the 'nix' package manager is
                                    installed
postgresql-database-exists          installs PostgreSQL (if necessary), and
                                    makes sure a specified database exists
postgresql-service                  ensures PostgrSQL service is installed
prometheus-mysqld-exporter-service  installs the Prometheus mysqld exporter
prometheus-node-exporter-service    installs the Prometheus node exporter
prometheus-service                  installs the Prometheus monitoring
                                    service
python-dev-project                  (Optionally) clone a Python project git
                                    repo, install the right version of
                                    Python using pyenv, create a virtualenv
                                    for the
python-packages-in-virtualenv       installs Python packages into a
                                    Virtualenv
python-virtualenv                   create a Python virtualenv
python-virtualenv-execute-shell     executes a command inside a virtualenv
python-virtualenv-exists            create a Python virtualenv
python-virtualenv-service           setup a service executing an application
                                    from within a virtualenv
runtime-python                      n/a
shell-output-to-file                execute a shell command, write the
                                    output to file
ssh-key-exists                      ensures an ssh key exists for a user
ssh-key-is-absent                   ensures an ssh key is absent for a user
sysctl-value                        set a sysctl value
systemd-service-unit                create and configure a certain systemd
                                    service unit exists
systemd-services-started            a list of init-service to start (if they
                                    exist) using Ansible
systemd-services-stopped            a list of init-service to stop (if they
                                    exist) using Ansible
user-exists                         make sure a user exists
webserver-service                   ensures a webserver is installed and
                                    running
webserver-static-site               install and configure webserver for
                                    static site
wordpress-folder-prepared           prepares wordpress project folders
wordpress-standalone                sets up a single-site wordpress instance
wordpress-vhost-apache              create Apache wordpress virtual host
                                    config
wordpress-vhost-nginx               create Nginx wordpress virtual host
                                    config
zerotier-network-member             add and authorize a new member to an
                                    existing zerotier network
```
</div>

The same list of *frecklets* can also be found online in the [default frecklet repository](https://freckles.io/frecklets/default).

If you want to see all tasks that are related to one (or several) search terms, use:

``` console
$ frecklecute --apropos TERM
```

So, as an example, for everything related to the term 'nginx', we'd see:

``` console
> frecklecute --apropos nginx

frecklet                  description
------------------------  -------------------------------------------------
devpi-nginx-vhost-config          creates a vhost for devpi on Nginx
devpi-service                     installs a complete devpi server,
                                  including nginx proxy & lets-encrypt certs
devpi-standalone                  installs a complete devpi server,
                                  including nginx proxy & lets-encrypt certs
nginx-inaugurate-vhost            creates a vhost to host a 'inaugurate'
                                  bootstrap script
nginx-reverse-proxy-vhost-config  n/a
nginx-vhost-from-folder           configure a Nginx vhost for static site
pkg-nginx                         ensures the nginx web server is installed
                                  and running
wordpress-vhost-nginx             create Nginx wordpress virtual host config
```

</div>
<!-- list available frecklets -->

<!-- display frecklets help -->

### Display *frecklet* help {: .block-title}

<div class="section-block" markdown="1">

Once you picked the *frecklet* you want to run, you can get it's usage information via:

```bash
> frecklecute FRECKLET --help
```

For example, the [``file-downloaded``](/frecklets/default/filesystem/file-downloaded/) frecklet yields:

```console
> frecklecute file-downloaded --help

Usage: frecklecute file-downloaded [OPTIONS] URL

  Download a file, create intermediate destination directories and a
  user/group if necessary.

  If no 'dest' option is provided, the file will be downloaded into
  '~/Downloads'.

  This uses the Ansible get_url module, check it's help for more details.

Options:
  --dest DEST           The destination file (or directory).  [default:
                        ~/Downloads/]
  --force / --no-force  Whether to force download/overwrite the target.
  --group GROUP         The group of the target file.
  --mode MODE           The mode the file should have, in octal (e.g. 0755).
  --owner USER          The owner of the target file.
  --help                Show this message and exit.

```

</div>
<!-- block display frecklet help -->

</div>
<!-- section installing freckles -->

<!-- section executing a command -->
## Executing a *frecklet*... {: .section-title}
<div class="section-block" markdown="1">

You can use the same *frecklet* on your local machine or remotely.

<!-- begin block locally -->
### ...locally {: .block-title}

<div class="section-block" markdown="1">

For local usage, you don't need to do anything special:

```console
> frecklecute file-downloaded --dest /tmp/my/temp/downloads/logo.svg https://frkl.io/images/frkl-logo-black.svg

╭╼ starting run
│  ├╼ running frecklet: file-downloaded (on: localhost)
│  │  ├╼ starting Ansible run
│  │  │  ├╼ create directory: /tmp/my/temp/downloads'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ download 'https://frkl.io/images/frkl-logo-black.svg -> /tmp/my/temp/downloads/logo.svg'
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok
```
</div>
<!-- end block locally -->

<!-- begin block remotely -->
### ...remotely {: .block-title}
<div class="section-block" markdown="1">

For this, you should have a ssh-server running on the target box. If you need root/sudo permissions for the task you want to run, you also need to connect as root, or have an account setup that can do password-less sudo (for which, of course, there also exists a [frecklet](/frecklets/default/system/passwordless-sudo-users)).

To login to a remote server, add the ``--target <user>@<hostname>`` flag before the *frecklet* name, e.g.:

```console
>  frecklecute --ask-ssh-pass --target pi@10.0.0.209 file-downloaded --dest /tmp/my/remote/download/path/logo.svg https://frkl.io/images/frkl-logo-black.svg

SSH PASS: ****

╭╼ starting run
│  ├╼ running frecklet: file-downloaded (on: 10.0.0.209)
│  │  ├╼ starting Ansible run
│  │  │  ├╼ create directory: /tmp/my/remote/download/path'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ download 'https://frkl.io/images/frkl-logo-black.svg -> /tmp/my/remote/download/path/logo.svg'
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok
```
</div>
<!-- end block remotely -->

</div>
<!-- section executing a command -->

<!-- begin section writing your own frecklet -->
## Writing your own *frecklets* {: .section-title}
<div class="section-block" markdown="1">

You might very well be happy enough to be able to run any of the prepared *frecklets* that ship with *frecklets*, or are available via the [community repository](/frecklets/community).

But maybe you'd like to combine a few of those *frecklets*, and create your own re-usable, share-able scripts, to do custom tasks? This is quite easy to do with *freckles*. All you need to know is how to create a [YAML](https://yaml.org) file, and assemble the tasks you need done.

<!-- begin block your first frecklet -->
### Your first *frecklet*
<div class="section-block" markdown="1">

To demonstrate how to combine multiple (pre-existing) *frecklets* into a new one, let's do some basic filesystem manipulation
that does not require root permissions. This example does not make a whole lot of sense, but demonstrates a few basic
 concepts.

 So, for the sake of argument let's assume we need to have an archive of a folder that contains a downloaded file, a
 readme file with certain content, and another file that contains the directory listing at the point just before the archiving.

 This is what needs to happen:

 - we need to create the directory that needs to be archived
 - we need to download a file into it
 - we need to create the text file inside the folder
 - we need to create the directory listing file inside the folder
 - we need to create the archive
 - we also should delete the directory, once the archive was created

After perusing the [frecklet index](/frecklets/default), we found we can use those *frecklets* for what we have to do:

- [file-downloaded](/frecklets/default/filesystem/file-downloaded/)
- [file-with-content](/frecklets/default/filesystem/file-with-content/)
- [command-output-to-file](/frecklets/default/filesystem/command-output-to-file/)
- [path-archived](/frecklets/default/filesystem/path-archived/)
- [path-is-absent](/frecklets/default/filesystem/path-is-absent/)

We don't need to actually create the directory, because a few of those *frecklets* would implicitly do that for us. For example the
[file-downloaded](/frecklets/default/filesystem/file-downloaded) *frecklet* will automatically create the (parent) directory that is indirectly specified with that *frecklets* ``dest`` parameter.

The most basic *frecklet* is a text file containing a list of other frecklets and their configuration,
in either 'yaml', 'json', or 'toml' format (for more details, head over to the [frecklet documentation](/doc/frecklets/)
section, and esp. the [Anatomy of a frecklet](/doc/frecklets/anatomy) page to learn the different ways a *frecklet* can look like).

Let's create a YAML file called ``my-first.frecklet``, with the following content:

```yaml
- file-downloaded:
    url: https://frkl.io/images/frkl-logo-black.svg
    dest: /tmp/target_dir/frkl-logo-black.svg
- file-with-content:
    path: /tmp/target_dir/readme.txt
    content: |
      Hi there!

      Welcome to the archive that contains this file we downloaded and other stuff.
- command-output-to-file:
    path: /tmp/target_dir/contents.txt
    command: "ls -l /tmp/target_dir"
- path-archived:
    path: /tmp/target_dir
    dest: /tmp/target_archive.zip
    format: zip
- path-is-absent:
    path: /tmp/target_dir
```

Once saved, we can execute this file with the ``frecklecute`` command:

```console
➜ frecklecute my-first.frecklet

╭╼ starting run
│  ├╼ running frecklet: /home/markus/my-first.frecklet (on: localhost)
│  │  ├╼ starting Ansible run
│  │  │  ├╼ create directory: /tmp/target_dir'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ download 'https://frkl.io/images/frkl-logo-black.svg -> /tmp/target_dir/frkl-logo-black.svg'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ write content to file: /tmp/target_dir/readme.txt
│  │  │  │  ╰╼ ok
│  │  │  ├╼ execute command: 'ls -l /tmp/target_dir'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ write command output to: /tmp/target_dir/contents.txt
│  │  │  │  ╰╼ ok
│  │  │  ├╼ archive path: /tmp/target_dir -> /tmp/target_archive.zip
│  │  │  │  ╰╼ ok
│  │  │  ├╼ delete file (if exists): /tmp/target_dir
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok
```

 **Hint**: for fun and giggles, try the ``--describe`` flag (``frecklecute --describe my-first.frecklet``)

 Now, if you know some shell scripting, you'll probably agree that this is nothing a small script could not have done
 equally well. So if you don't think this whole thing makes any sense so far, head on down to the next examples.

 The *frecklet* schema is designed to be easy and quick to read, understand and write. Whether the above
 code fits that bill or not is up to you to decide. One thing to point out though is the absence of any intermediate (sub-)tasks that
 are implied in a (parent-)task.

 Take, for example, ``file-downloaded``. As we always need a target folder for our downloaded file to exist,
 and as that target folder path is clear from the ``dest`` parameter the user provides, it (arguably -- there are some caveats)
  makes sense to always create that folder automatically. Similarly, had we set the  ``owner`` parameter of the same *frecklet*, it would have been
 implicit that a user with that name needs to exist on the system, and *freckles* had created that user. That would have required
 'root' or 'sudo' permissions, though.

 On a side-note: whether all of those implicit tasks are done automatically or not depends entirely on how the 'child'
 *frecklets* in a [freckles context](https:/TODO) are implemented. The *freckles* default context is written with an eye
 on [immutable infrastructure](https://www.digitalocean.com/community/tutorials/what-is-immutable-infrastructure), in a way so *frecklets*
 require as little information and manual specification as possible from the user, and they will just do the sensible thing.
 You could write your own *context* though, with *frecklets* that needs all of those steps specified explicitly.



</div>
<!-- end block your first frecklet -->

<!-- begin block your first parameters -->
### Adding parameters
<div class="section-block" markdown="1">

One of the neat things about *freckles* is that it is very easy to turn a *frecklet* into a full-blown commandline script,
including argument parsing.

So, let's say we want the download url as well as the path of the archive to be user configurable. Let's do that, and
while we're at it let's also add a [shebang line](https://en.wikipedia.org/wiki/Shebang_(Unix)) to our script so we can execute it
directly. Let's create a new file, ``my-second.frecklet``:

```yaml
#!/usr/bin/env frecklecute

- file-downloaded:
    url: "{{:: file_url ::}}"
    dest: /tmp/target_dir/
- file-with-content:
    path: /tmp/target_dir/readme.txt
    content: |
      Hi there!

      Welcome to the archive that contains this file we downloaded from {{:: file_url ::}} and other stuff.
- command-output-to-file:
    path: /tmp/target_dir/contents.txt
    command: "ls -l /tmp/target_dir"
- path-archived:
    path: /tmp/target_dir
    dest: "{{:: archive_path ::}}"
    format: zip
- path-is-absent:
    path: /tmp/target_dir
```

*freckles* uses the [jinja2](http://jinja.pocoo.org/) templating engine (with its own block markers) to let users specify
arguments. By default, all jinja variables will be turned into an argument that is non-optional, and can't be empty. Let's see:

```console
> chmod +x my-second.frecklet   # to make the file executable
> ./my-second.frecklet --help

Usage: frecklecute ./my-second.frecklet [OPTIONS]

  n/a

Options:
  --archive-path ARCHIVE_PATH  n/a  [required]
  --file-url FILE_URL          n/a  [required]
  --help                       Show this message and exit.
```

Now try to actually provide those new arguments:

```console
> ./my-second.frecklet --file-url https://frkl.io/images/frkl-logo-black.svg --archive-path /tmp/my_custom_path.zip

╭╼ starting run
│  ├╼ running frecklet: /home/markus/my-second.frecklet (on: localhost)
│  │  ├╼ starting Ansible run
│  │  │  ├╼ create directory: /tmp/target_dir/'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ download 'https://frkl.io/images/frkl-logo-black.svg -> /tmp/target_dir/'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ write content to file: /tmp/target_dir/readme.txt
│  │  │  │  ╰╼ ok
│  │  │  ├╼ execute command: 'ls -l /tmp/target_dir'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ write command output to: /tmp/target_dir/contents.txt
│  │  │  │  ╰╼ ok
│  │  │  ├╼ archive path: /tmp/target_dir -> /tmp/my_custom_path.zip
│  │  │  │  ╰╼ ok
│  │  │  ├╼ delete file (if exists): /tmp/target_dir
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok
```

</div>

There is a lot more you can do to make the script more usable, for example add documentation, and specify argument types
so *freckles* can validate user input. Check out the [frecklet documentation](/doc/frecklets) and particularly the page about
[the evolution of a *frecklet*](/doc/frecklets/evolution) to learn more.

<!-- end block your first parameters -->

<!-- begin block real-life example -->
### A real-life example
<div class="section-block" markdown="1">

To see how useful *freckles* can be, we need a task that isn't as easy to script in a shell as the above. How about
setting up machine so it can host a static web-page? It's a fairly simple task when using *freckles*, but would take
considerable determination to reliably script in bash.

What needs to be done? Here's a list:

- install a web-server (Nginx, in this instance)
- configure it properly for our task (serve a folder of static html pages)
- upload our html page(s)

Again, we check the [default](/frecklets/default) and [community](/frecklets/community) frecklet indexes for any pre-written
*frecklets* we can use. Actually, there is already a [*frecklet* to setup and configure a static website](/frecklets/default/web/webserver-static-site/)
. But let's pretend it did not and go a tiny bit lower level.

So, here are the *frecklets* we are going to use:

- [``nginx-vhost-from-folder``](/frecklets/default/service/nginx-vhost-from-folder/), to create the vhost/server-block configuration file
- [``webserver-service``](/frecklets/default/service/webserver-service/), to setup and configure Nginx
- [``file-with-content``](/frecklets/default/filesystem/file-with-content/), to create the html file

**Note**: Under the hood we are taking advantage of a few [Ansible roles](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html) (particularly [``geerlingguy.nginx``](https://github.com/geerlingguy/ansible-role-nginx)) to do the hard work for us.

Here's what our new *frecklet* looks like (let's save it to a file called ``my-webserver.frecklet``):

```yaml
- nginx-vhost-from-folder:  
    hostname: "{{:: hostname ::}}"  
- webserver-service:  
    webserver: nginx  
- file-with-content:  
    owner: www-data  
    path: /var/www/html/index.html  
    content: |  
      <h1><i>freckles</i> says "hello", {{:: helloee ::}}!</h1>  
```

As in the example above, we made some of our script configurable via arguments (the 'hostname', and part of the html page content, 'helloee') and we could
use the ``--help`` flag on our *frecklet* to see that.

For this example, I don't want to run it on my local machine, as it would install a web-server that I have no use for on there. So I went to a VPS (Virtual private server) provider and rented a machine in the cloud, set up DNS and security so there's an admin user that has password-less sudo permissions, and that I can access using my local ssh key. All this goes to far for this tutorial, but I'll write up instructions sometime soon (or, rather, a few *frecklets* to do it for you), in a different place. For now, just peruse your favourite search engine if you want to know more.

Ok, execute time:

<div class="code-max-height" markdown="1">

```console
> frecklecute  -t admin@dev.frkl.io my-webserver.frecklet --hostname dev.frkl.io --helloee World

╭╼ starting run
│  ├╼ running frecklet: /home/markus/my-webserver.frecklet (on: dev.frkl.io)
│  │  ├╼ starting Ansible run
│  │  │  ├╼ create directory: /etc/nginx/sites-enabled'
│  │  │  │  ╰╼ ok
│  │  │  ├╼ write content to file: /etc/nginx/sites-enabled/dev.frkl.io.http.conf
│  │  │  │  ╰╼ ok
│  │  │  ├╼ creating webserver user
│  │  │  │  ╰╼ ok
│  │  │  ├╼ Ensure nginx is installed.
│  │  │  │  ╰╼ ok
│  │  │  ├╼ Remove default nginx vhost config file (if configured).
│  │  │  │  ╰╼ ok
│  │  │  ├╼ restart nginx
│  │  │  │  ╰╼ ok
│  │  │  ├╼ Copy nginx configuration in place.
│  │  │  │  ╰╼ ok
│  │  │  ├╼ reload nginx
│  │  │  │  ╰╼ ok
│  │  │  ├╼ reloading webserver
│  │  │  │  ╰╼ ok
│  │  │  ├╼ ensure user 'www-data' exists
│  │  │  │  ╰╼ ok
│  │  │  ├╼ write content to file: /var/www/html/index.html
│  │  │  │  ╰╼ ok
│  │  │  ├╼ geerlingguy.nginx : restart nginx
│  │  │  │  ╰╼ ok
│  │  │  ├╼ geerlingguy.nginx : reload nginx
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok

```

</div>

Now, to check if this worked, I visit the hostname I specified ('dev.frkl.io', in this case) with my browser, and should see:

```
freckles says "hello", World!
```

It'd be really easy to change this *frecklet* to, for example, upload a local folder with html files instead of creating the single
file on the server, support https via [Let's encrypt](https://letsencrypt.org), add a firewall, etc. The *frecklet* would only grow by a few lines. All this exceeds the scope of this 'getting started'-guide though.
Check out the [Documentation](/doc) if you want to learn more!

<!-- end block real-life example -->

</div>

</div>
<!-- end section writing your own frecklet -->
