nav_priority: 2
title: Getting started

## Installing *freckles*

There are several ways to install the *freckles* package. For the purpose of getting started quickly, we'll use the recommended way, a [bootstrap script](https://gitlab.com/frkl/inaugurate).

Apart from installing the *freckles* package, this script can execute one of the applications that come with it straight away, as well as uninstall the whole she-bang after execution (if so desired). For now we don't have to concern ourselves with any of those more advanced features, all we want to do is get *freckles* onto our machine:

```
curl https://freckles.sh | bash
```

or, if we don't have ``curl`` but only ``wget`` available (as is the case on a vanilla 'Debian' install, for example):

```
wget -O- https://freckles.sh | bash
```

This will install *freckles* in ``$HOME/.local/share/inaugurate/``, for more details about this process check [here](https://gitlab.com/frkl/inaugurate#how-does-this-work-what-does-it-do).

To have the *freckles* commands available in your shell session now, we have to source the ``.profile`` file:

```bash
source ~/.profile
```

## List available *frecklets*

*freckles* operates on lists of tasks, each such list of tasks is called a *frecklet*. A *frecklet* contains one or more task items, of which each one can either be a low-level, atomic operation (e.g. 'create a directory'), or another *frecklet* (which typically encapsulates a higher-level objective, like for example 'setup a wordpress instance').

The *freckles* package comes with several commandline executables, the one you'll probably use most in the beginning is called ``frecklecute`` and it lets you execute pre-written and included *frecklets* (typically installing and configuring a service), as well as your own.

Let's get a list of all the *frecklets* that are supported out of the box:

```
frecklecute --help
```
This will show something like this:
```
Usage: frecklecute [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --config TEXT     select config profile(s)
  --community           allow resources from the freckles community repo
  -r, --repo TEXT       additional repo(s) to use
  -h, --host TEXT       the host to use
  --ask-pass            ask for the connection password
  -o, --output TEXT     the output format to use
  -v, --vars VARS_TYPE  additional vars, higher priority than frecklet vars,
                        lower priority than potential user input
  -e, --elevated        indicate that this run needs elevated permissions
  -ne, --not-elevated   indicate that this run doesn't need elevated
                        permissions
  --no-run              create the run environment (if applicable), but don't
                        run the frecklet
  --version             the version of freckles you are using
  --verbosity LVL       Either CRITICAL, ERROR, WARNING, INFO or DEBUG
  --apropos TAG         Show this message, listing all commands that contain
                        this value in their name or description.
  --help-all            Show this message, listing all possible commands.
  --help                Show this message and exit.

Commands:
  admin-user-exists               ensures admin user with a specified username
                                  exists
  devpi-nginx-vhost-config-exists
                                  creates a vhost for devpi on Nginx
  file-downloaded                 downloads file
  file-exists                     ensures a file exists
  file-exists-with-content        ensures a file exists and its content is the
                                  one specified as input
  folder-exists                   ensures a folder exists
  lang-go-installed               make sure Go is available
  lang-java-installed             make sure OpenJDK is available
  ...
  ...
```
If you want to see all available tasks, not just the featured ones, you can do:

```bash
frecklecute --help-all
```

The same list of *frecklets* can also be found online: [frecklets](/frecklet-index).

If you want to see all tasks that are related to one (or several) search terms, use:

``` bash
frecklecute --apropos <term>
```

E.g.:

``` bash
$ frecklecute --apropos nginx
Usage: frecklecute [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --config TEXT     select config profile(s)
  ...
  ...
  ...
  --help-all            Show this message, listing all possible commands.
  --help                Show this message and exit.

Commands:
  devpi-nginx-vhost-config-exists
                                  creates a vhost for devpi on Nginx
  nginx-vhost-config              ensure file exists with content of the
                                  'nginx_server_block' templig
  pkg-nginx-installed             ensures the nginx web server is installed
                                  and running
  service-devpi                   installs a complete devpi server, including
                                  nginx proxy & lets-encrypt certs
  webserver-prepared              ensures a webserver is installed and running
  ...
  ...
```

## Getting help

Once you picked the *frecklet* you want to run, you can get it's usage information via:

```bash
frecklecute <frecklet_name> --help
```

E.g.:

```
$ frecklecute file-downloaded --help
Usage: frecklecute file-downloaded [OPTIONS] URL

  Downloads a file, creates intermediate destination directories and a
  user/group if necessary.

  If no 'dest' option is provided, the file will be downloaded into
  '~/Downloads'.

  This uses the [Ansible get_url module](https://docs.ansible.com/ansible/la
  test/modules/get_url_module.html), check it's help for more details.

Options:
  --become       Whether to use root privileges to do the downloading and
                 saving.  [default: False]
  --dest DEST    The destination file (or directory).  [default: ~/Downloads/]
  --force        Whether to force download/overwrite the target.  [default:
                 False]
  --group GROUP  The group of the target file.
  --mode MODE    The mode the file should have, in octal (e.g. 0755).
  --owner USER   The owner of the target file.
  --help         Show this message and exit.
```

## Executing a *frecklet*

You can use the same *frecklet* on your local machine, as well as remotely.

### locally

For local usage, you don't need to do anything special:

```bash
frecklecute file-downloaded --dest /tmp/my/temp/downloads/logo.svg https://frkl.io/images/frkl-logo-black.svg
```

??? Abstract "command output"
    ```
    ╭─ starting: 'file-downloaded'
    ├╼ connector: nsbl
    │  ├╼ host: localhost
    │  │  ├╼ starting playbook
    │  │  │  ╰╼ ok
    │  │  │  ├╼ checking if parent folder exists
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ creating parent directory for: /tmp/my/temp/downloads/logo.svg'
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ downloading 'https://frkl.io/images/frkl-logo-black.svg -> /tmp/my/temp/downloads/logo.svg'
    │  │  │  │  ╰╼ ok
    │  │  │  ╰╼ ok
    │  │  ╰╼ ok
    │  ╰╼ ok
    ╰─ ok

    ```

### remotely

For this, you should have a ssh-server running on the target box. If you need root/sudo permissions for the task you want to run, you also need to connect as root, or have an account setup that can do passwordless sudo (which you can setup using a [frecklet](/frecklet-index/default/grant-passwordless-sudo/), by the way).

To login to a remote server, add the ``--host <user>@<hostname>`` flag before the *frecklet* name, e.g.:

```bash
frecklecute --ask-pass --host pi@10.0.0.209 file-downloaded --dest /tmp/my/remote/download/path/logo.svg https://frkl.io/images/frkl-logo-black.svg
```

??? Abstract "command output"
    ```
    SSH PASS: xxxx

    ╭─ starting: 'file-downloaded'
    ├╼ connector: nsbl
    │  ├╼ host: 10.0.0.209
    │  │  ├╼ starting playbook
    │  │  │  ╰╼ ok
    │  │  │  ├╼ checking if parent folder exists
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ creating parent directory for: /tmp/my/remote/download/path/logo.svg'
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ downloading 'https://frkl.io/images/frkl-logo-black.svg -> /tmp/my/remote/download/path/logo.svg'
    │  │  │  │  ╰╼ ok
    │  │  │  ╰╼ ok
    │  │  ╰╼ ok
    │  ╰╼ ok
    ╰─ ok
    ```

## Writing your own *frecklet*

You might very well be happy enough to be able to run any of the prepared *frecklets* that ship with *frecklets*, or are available via the [community repository](https://TODO).

But maybe you'd like to combine a few of those *frecklets*, and create your own re-usable, share-able scripts, to do custom tasks? This is quite easy to do with *freckles*. All you need to know is how to create a [YAML](https://yaml.org) file (let's call it ``hello-world.frecklet``), and assemble the tasks you need done.

In our example, let's install a webserver, configure it properly for our task, and let it serve a single, static html page. For that we use the [``nginx-vhost-config``](https://TODO), [``webserver-prepared``](/frecklet-index/default/webserver-prepared) and [``file-exists-with-content``](/frecklet-index/default/file-exists-with-content) *frecklets*:

```yaml
- nginx-vhost-config:
    path: /etc/nginx/sites-enabled/example.conf
    document_root: /var/www/html
    become: true
- webserver-prepared:                  # by default, nginx is used
    document_root: /var/www/html
- file-exists-with-content:
    owner: www-data
    path: /var/www/html/index.html
    become: true
    content: |
      <h1><i>freckles</i> says "hello", World!</h1>
```

!!! note
    You probably don't want to execute this command on your local machine, as you most likley don't want a webserver running. If you want to try this out, maybe use [Vagrant](https://vagrantup.com) or a [Docker](https://docker.com) container.

This is how we execute our newly created script:

```bash
frecklecute hello-world.frecklet
```

??? abstract "command output"

    ```
    $ frecklecute hello-world.frecklet
    SUDO_PASSWORD: xxxx
    ╭─ starting: 'hello-world'
    ├╼ connector: nsbl
    │  ├╼ host: localhost
    │  │  ├╼ starting playbook
    │  │  │  ├╼ doing freckly init stuff, may take a while
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ installing webserver
    │  │  │  │  ├╼ include_tasks
    │  │  │  │  │  ├╼ setting webserver defaults
    │  │  │  │  │  │  ╰╼ ok
    │  │  │  │  │  ├╼ setting webserver user
    │  │  │  │  │  │  ╰╼ ok
    │  │  │  │  │  ├╼ setting webserver_group
    │  │  │  │  │  │  ╰╼ ok
    │  │  │  │  │  ├╼ setting webserver_service_name
    │  │  │  │  │  │  ╰╼ ok
    │  │  │  │  │  ├╼ setting webserver-specific variables
    │  │  │  │  │  │  ├╼ basic auth
    │  │  │  │  │  │  │  ╰╼ ok
    │  │  │  │  │  │  ├╼ setting variables for non-https deployment
    │  │  │  │  │  │  │  ╰╼ ok
    │  │  │  │  │  │  ├╼ setting nginx vhosts vars
    │  │  │  │  │  │  │  ╰╼ ok
    │  │  │  │  │  │  ├╼ setting various nginx vars
    │  │  │  │  │  │  │  ╰╼ ok
    │  │  │  │  ├╼ include_tasks
    │  │  │  ├╼ Include OS-specific variables.
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ include_tasks
    │  │  │  │  ├╼ Update apt cache.
    │  │  │  │  │  ╰╼ ok
    │  │  │  │  ├╼ Ensure nginx is installed.
    │  │  │  │  │  ╰╼ ok
    │  │  │  ├╼ Remove default nginx vhost config file (if configured).
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ Ensure nginx_vhost_path exists.
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ Add managed vhost config files.
    │  │  │  │  ├╼ {u'extra_parameters': u'\n\n\n\n# letsencrypt\n# not applicable\n\n# ssl options\n\n\n', u'listen': u'80 ', u'root': u'/var/www/html', u'server_name': u'localhost', u'filename': u'localhost.80.conf'}
    │  │  │  │  │  ╰╼ ok
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ Remove legacy vhosts.conf file.
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ Copy nginx configuration in place.
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ Ensure nginx is started and enabled to start at boot.
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ checking parent folder stats
    │  │  │  │  ╰╼ ok
    │  │  │  ├╼ writing content to file: /var/www/html/index.html
    │  │  │  │  ╰╼ ok
    │  │  │  ╰╼ ok
    │  │  ╰╼ ok
    │  ╰╼ ok
    ╰─ ok
    ```

!!! note
    This would ask you for the sudo password, as it needs to install packages via the system package manager.

Visiting [http://localhost](http://localhost) should show you our newly created page.
