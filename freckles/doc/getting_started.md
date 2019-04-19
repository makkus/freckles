---
url_path_prio: 1
title: Getting started
---

## Installing *freckles* {: .section-title}

<div class="section-block" markdown="1">

There are several ways to install *freckles*. The simplest one is to just download the binary for your platform:

- [Linux](https://pkgs.freckles.sh/downloads/linux-gnu/freckles)
- [Mac OS X](https://pkgs.freckles.sh/downloads/darwin15/freckles)
- Windows is not supported directly, but you can use the [Linux version](https://pkgs.freckles.sh/downloads/linux-gnu/freckles) on [WSL](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux)

Make the file executable and copy it into a folder on your ``PATH`` (e.g. ``/usr/local/bin``). If you intend to also use the ``frecklecute`` application (and you probably want to), also 'link' the file to that name (as the binary contains both the ``freckles`` and ``frecklecute`` applications). Here's how you could do all this (on Linux):

```console
wget https://pkgs.frkl.io/downloads/linux-gnu/freckles
chmod +x freckles
sudo mv freckles /usr/local/bin
sudo ln -s /usr/local/bin/freckles /usr/local/bin/frecklecute
``` 

For the purpose of getting started quickly, you could also use the [*freckles* bootstrap script](https://gitlab.com/freckles-io/freck), which achieves something similar to the above:

```console
curl https://freckles.sh | bash
# or
wget -O- https://freckles.sh | bash
```

This adds a section to your ``$HOME/.profile`` to make *freckles* available in your ``$PATH``. For that to be the case, you either have to logout and re-login to your session, or source the ``.profile`` file:

```console
source ~/.profile
```

For other install options, check [here](/doc/installation).

</div>

## Getting help {: .section-title}
<div class="section-block" markdown="1">

*freckles* operates on lists of tasks, each such list of tasks is called a *frecklet*. A *frecklet* contains one or more task items, of which each one can either be a low-level, atomic operation (e.g. 'create a directory'), or another *frecklet* (which typically encapsulates a higher-level objective, like for example 'setup a wordpress instance').

The *freckles* package comes with several commandline applications, the one you'll probably use most in the beginning is called ``frecklecute`` and it lets you execute a set of *frecklets* that are shipped with *freckles* by default (typically installing and configuring a service), as well as your own ones. 

To display help for ``frecklecute`` (as well as any of the other included applications), use the ``--help`` flag:

```console
$ frecklecute --help

Usage: frecklecute [OPTIONS] FRECKLET [ARGS]

  Execute frecklets using an auto-generated command-line interface.

  frecklecute supports executing any frecklet that is available in the
  current context as well as external ones. If the selected FRECKLET option
  is a file and exists, it will be parsed, validated, and executed. If not,
  a context-lookup will be performed and, if found, that frecklet will be
  used.

  Use the '--help-frecklets' option to get a list of all available frecklets
  in the current context.

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
  --help-frecklets      Show this message, listing all available frecklets.
  --help                Show this message

  frecklecute is part of the 'freckles' project. It is free to use in
  combination with open source software. For more information on licensing
  and documentation please visit: https://freckles.io
```

### List available *frecklets* {: .block-title}

<div class="section-block" markdown="1">

Let's get a list of all the *frecklets* that are supported out of the box, use the ``--help-frecklets`` flag (this might take a few seconds, to process the current context):

```console
$ frecklecute --help-frecklets

Usage: frecklecute [OPTIONS] FRECKLET [ARGS]

  Execute frecklets using an auto-generated command-line interface.

  frecklecute supports executing any frecklet that is available in the
  ...
  ...
  --help                Show this message

Commands:
  admin-user-exists               ensure an admin user with a specified
                                  username exists
  apache-vhost-config             ensure file exists with content of the
                                  'apache_vhost' templig
  execute-ad-hoc-script           create an executable file from a template,
                                  execute it, delete it
  execute-command                 execute a one-off command
  ...
  ...
```

The same list of *frecklets* can also be found online: [frecklets](https://freckles.io/contexts/default/overview/).

If you want to see all tasks that are related to one (or several) search terms, use:

``` console
$ frecklecute --apropos <term>
```

E.g.:

``` console
$ frecklecute --apropos nginx
Usage: frecklecute [OPTIONS] FRECKLET [ARGS]...

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
</div>

### Display *frecklet* help {: .block-title}

<div class="section-block" markdown="1">

Once you picked the *frecklet* you want to run, you can get it's usage information via:

```bash
frecklecute <frecklet_name> --help
```

E.g.:

```console
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
</div>
</div>

## Executing a *frecklet* {: .section-title}
<div class="section-block" markdown="1">

You can use the same *frecklet* on your local machine, as well as remotely.

### locally {: .block-title}

<div class="section-block" markdown="1">

For local usage, you don't need to do anything special:

```console
frecklecute file-downloaded --dest /tmp/my/temp/downloads/logo.svg https://frkl.io/images/frkl-logo-black.svg
```

??? Abstract "command output"
    ```console
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

</div>

### remotely {: .block-title}

<div class="section-block" markdown="1">

For this, you should have a ssh-server running on the target box. If you need root/sudo permissions for the task you want to run, you also need to connect as root, or have an account setup that can do passwordless sudo (which you can setup using a [frecklet](/frecklet-index/default/grant-passwordless-sudo/), by the way).

To login to a remote server, add the ``--host <user>@<hostname>`` flag before the *frecklet* name, e.g.:

```console
frecklecute --ask-pass --host pi@10.0.0.209 file-downloaded --dest /tmp/my/remote/download/path/logo.svg https://frkl.io/images/frkl-logo-black.svg
```

??? Abstract "command output"
    ```console
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
</div>
</div>

## Writing your own *frecklet* {: .section-title}

<div class="section-block" markdown="1">

You might very well be happy enough to be able to run any of the prepared *frecklets* that ship with *frecklets*, or are available via the [community repository](https://TODO).

But maybe you'd like to combine a few of those *frecklets*, and create your own re-usable, share-able scripts, to do custom tasks? This is quite easy to do with *freckles*. All you need to know is how to create a [YAML](https://yaml.org) file (let's call it ``hello-world.frecklet``), and assemble the tasks you need done.

In our example, let's install a webserver, configure it properly for our task, and let it serve a single, static html page. For that we use the [``nginx-vhost-config``](https://TODO), [``webserver-prepared``](/frecklet-index/default/webserver-prepared) and [``file-has-content``](/frecklet-index/default/file-has-content) *frecklets*:

```yaml
- nginx-vhost-config:
    path: /etc/nginx/sites-enabled/example.conf
    document_root: /var/www/html
    become: true
- webserver-prepared:                  # by default, nginx is used
    document_root: /var/www/html
- file-has-content:
    owner: www-data
    path: /var/www/html/index.html
    become: true
    content: |
      <h1><i>freckles</i> says "hello", World!</h1>
```

!!! note
    You probably don't want to execute this command on your local machine, as you most likley don't want a webserver running. If you want to try this out, maybe use [Vagrant](https://vagrantup.com) or a [Docker](https://docker.com) container.

This is how we execute our newly created script:

```console
frecklecute hello-world.frecklet
```

??? abstract "command output"

    ```console
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
</div>
