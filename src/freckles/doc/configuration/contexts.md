---
title: Contexts
url_path_prio: 10
---


Each freckles run happens in a so-called 'context'. A 'context' is a set of configuration values that determine where
*frecklets* and other resources are allowed to come from, which *frecklets* are available to run, and how the execution of those *frecklets* happens. Multiple contexts can be combined for a single execution, for advanced use-cases and user-convenience.

Context definitions are stored (with the ending ``.context``) under ``$HOME/.config/freckles``. They are text files in yaml format, the filename (before the ``.context`` part) indicates the name of the context.

If no file for the 'default' context (file: ``$HOME/.config/freckles/default.context``) exists, the internal defaults
for every configuration option is used. This should provide a reasonable useful and secure environment for non-advanced usage. It allows only the execution of inbuilt [default](/frecklets/default) or [community](/frecklets/community) (with the ``--community`` commandline flag), or local *frecklets*.

If a user wants to start using other, remote *frecklet* repositories, or change potentially dangerous configuration settings, they have to 'unlock' the *freckles* configuration by actively accepting the *freckles* license. This can be either done by issuing the command:

```console
freckles context unlock
```

or do it manually, using a text-editor, by creating the 'default' context file (``$HOME/.config/freckles/default.context``) and add the line:

```yaml
accept_freckles_license: true
```

Once this is done, the user can use custom configuration options via the command-line, or add custom context files.

## The 'context' sub-command {: .section-title}
<div class="section-block" markdown="1">


The ``freckles`` command-line application comes with a ``context`` subcommand:

```console
freckles context --help

Usage: freckles context [OPTIONS] COMMAND [ARGS]...

...
...
...

Options:
  --help  Show this message and exit.

Commands:
  add     add a context configuration from a template
  copy    copy current configuration to new context
  delete  delete configuration profile
  doc     display documentation for config keys
  edit    edit a context configuration
  list    list all available contexts
  show    print current configuration
  unlock  unlock configuration for advanced usage

```

Those are convenience methods to create, edit, and display *freckles* contexts. Everything provided there can also be done
manually with a text-editor, if that is your preference. The commands are documented (``freckles context <comamnd_name> --help``), so we don't need to go into too much detail here and only show a main concepts and things that can be done.

</div>

### Configuration docs {: .block-title}
<div class="section-block" markdown="1">

Before changing some settings, it's probably a good idea to find out which settings are available. *freckles* tries provide
a useful set of defaults, but also exposes as many configuration options as possible to be able to support to as many use-cases and user preferences as possible.

That's why *freckles* has a whole in-build auto-documenting, and -validating configuration sub-system. Every *freckles* sub-system comes with it's own schema of supported settings. Some of them accept some of the same keys, some have their own, and some are not configurable at all. Every sub-system has a so-called configuration 'interpreter' (e.g. ``adapter_config_nsbl``, ``adapter_run_config_nsbl`` in the output below).


To see a list of all configuration options, issue:

<div class="code-max-height" markdown="1">

```console
freckles context doc

context

 adapters (list, default: ['nsbl', 'tempting', 'freckles'])
    A list of freckles adapters to use in this context.
 add_adapter_name_to_env (boolean, default: true)
    whether to add the adapter name to the run environment folder name
 add_timestamp_to_env (boolean, default: true)
    whether to add a timestamp to the run environment folder name
 allow_remote (boolean, default: false)
    Allow all remote repositories.
 allow_remote_whitelist (list, default: ['https://gitlab.com/frecklets/*'])
    List of urls (or url regexes) of allowed remote repositories.
 ask_user (string, default: none)
    when to ask the user for interactive input
 callback (['string', 'dict', 'list'], default: ['auto'])
    a list of callbacks to attach to a freckles run
 current_run_folder (string, default: /home/markus/.local/share/freckles/runs/current)
    target of a symlink the current run environment
 force_run_folder (boolean, default: true)
    overwrite a potentially already existing run environment
 ignore_empty_repos (boolean, default: true)
    Whether to ignore non-existent or empty local repos or fail if one such is encountered.
 keep_run_folder (boolean, default: false)
    whether to keep the run folder with the adapter environment after a run
 remote_cache_valid_time (integer, default: 0)
    Update remote repos if their last checkout was longer ago than this threshold.
 repos (list, default: ['default', 'user', './.freckles'])
    A list of repositories containing frecklets and/or associated resources.
 run_folder (string, default: /home/markus/.local/share/freckles/runs/archive/run)
    the target for the generated run environment

adapter_config_nsbl

 allow_remote (boolean, default: false)
    whether to allow remote roles and/or tasklists, can be overwritten by 'allow_remote_roles' and 'allow_remote_tasklists'
 allow_remote_roles (boolean)
    whether to allow remote roles
 allow_remote_tasklists (boolean)
    whether to allow remote tasklists
 force_show_log (boolean, default: false)
    disable the hiding of task details when those contain secret variables, only use this for debugging purposes

adapter_run_config_nsbl

 connection_type (string)
    the connection type, probably 'ssh' or 'local'
 elevated (boolean)
    this run needs elevated permissions
 host (string, default: localhost)
    the host to connect to
 host_ip (string)
    the host ip, optional
 minimal_facts_only (boolean, default: false)
    whether to not execute basic box tasks (install python, etc.). Most likely you want that set to False.
 no_run (boolean)
    only create the Ansible environment, don't execute any playbooks
 output (string)
    the callback name
 passwordless_sudo (boolean)
    the user can do passwordless sudo on the host where those tasks are run
 port (integer, default: 22)
    the ssh port to connect to in case of a ssh connection
 run_callback (unknown_type)
    the output callback to use
 ssh_key (string)
    the path to a ssh key identity file
 use_ara (boolean, default: false)
    whether to use ara (https://ara.readthedocs.io)
 use_mitogen (boolean, default: false)
    whether to use mitogen to speed up Ansible playbook execution
 user (string)
    the user name to use for the connection

adapter_config_tempting

  No config schema

adapter_run_config_tempting

  No config schema

adapter_config_freckles

  No config schema

adapter_run_config_freckles

  No config schema
```

</div>



</div>

### Context details {: .block-title}
<div class="section-block" markdown="1">

To display the settings of your current context you can execute the following command (in this case, ``latest`` is the name of the context we are interested in:

<div class="code-max-height" markdown="1">

```console
 freckles -c latest context show

accept_freckles_license: true
adapters:
- nsbl
- tempting
- freckles
add_adapter_name_to_env: true
add_timestamp_to_env: true
allow_remote: false
allow_remote_whitelist:
- https://gitlab.com/frecklets/*
ask_user: none
callback:
- auto
current_run_folder: /home/markus/.local/share/freckles/runs/current
force: true
ignore_empty_repos: true
keep_run_folder: false
remote_cache_valid_time: 0
repos:
- 'frecklets::gl:frecklets/frecklets-nsbl-default::develop::'
- 'frecklets::gl:frecklets/frecklets-nsbl-community::develop::'
- 'roles::gl:frecklets/frecklets-nsbl-default-resources::develop::'
- 'ansible-tasklists::gl:frecklets/frecklets-nsbl-default-resources::develop::'
- 'temptings::gl:frecklets/temptings-default::develop::'
- 'roles::gl:frecklets/frecklets-nsbl-community-resources::develop::'
- 'ansible-tasklists::gl:frecklets/frecklets-nsbl-community::develop::'
- user
- ./.freckles
run_folder: /home/markus/.local/share/freckles/runs/archive/run
```

</div>

If we had an 'augmented' context, we could do something like:

```console
freckles -c latest -c dev -c callback=result context show
...
...
```

More interesting output -- but also way more verbose -- is produced by using the '--show-interpreters' flag. This incorporates the same information as the ``freckles context doc`` command, but also shows the current (somtimes post-processed) value for every *freckles* sub-system:

<div class="code-max-height" markdown="1">

```console
➜ freckles -c latest context show -i

Configuration
-------------

  accept_freckles_license: true
  adapters:
  - nsbl
  - tempting
  - freckles
  add_adapter_name_to_env: true
  add_timestamp_to_env: true
  allow_remote: false
  allow_remote_whitelist:
  - https://gitlab.com/frecklets/*
  ask_user: none
  callback:
  - auto
  current_run_folder: /home/markus/.local/share/freckles/runs/current
  force: true
  ignore_empty_repos: true
  keep_run_folder: false
  remote_cache_valid_time: 0
  repos:
  - 'frecklets::gl:frecklets/frecklets-nsbl-default::develop::'
  - 'frecklets::gl:frecklets/frecklets-nsbl-community::develop::'
  - 'roles::gl:frecklets/frecklets-nsbl-default-resources::develop::'
  - 'ansible-tasklists::gl:frecklets/frecklets-nsbl-default-resources::develop::'
  - 'temptings::gl:frecklets/temptings-default::develop::'
  - 'roles::gl:frecklets/frecklets-nsbl-community-resources::develop::'
  - 'ansible-tasklists::gl:frecklets/frecklets-nsbl-community::develop::'
  - user
  - ./.freckles
  run_folder: /home/markus/.local/share/freckles/runs/archive/run


Interpreters
------------

  context

    adapters:
      desc: A list of freckles adapters to use in this context.
      current value:
      - nsbl
      - tempting
      - freckles
      default:
      - nsbl
      - tempting
      - freckles
    add_adapter_name_to_env:
      desc: whether to add the adapter name to the run environment folder name
      current value: true
      default: true
    add_timestamp_to_env:
      desc: whether to add a timestamp to the run environment folder name
      current value: true
      default: true
    allow_remote:
      desc: Allow all remote repositories.
      current value: false
      default: false
    allow_remote_whitelist:
      desc: List of urls (or url regexes) of allowed remote repositories.
      current value:
      - https://gitlab.com/frecklets/*
      default:
      - https://gitlab.com/frecklets/*
    ask_user:
      desc: when to ask the user for interactive input
      current value: none
      default: none
    callback:
      desc: a list of callbacks to attach to a freckles run
      current value: freckles_callback
      default:
      - auto
    current_run_folder:
      desc: target of a symlink the current run environment
      current value: /home/markus/.local/share/freckles/runs/current
      default: /home/markus/.local/share/freckles/runs/current
    force_run_folder:
      desc: overwrite a potentially already existing run environment
      current value: n/a
      default: true
    ignore_empty_repos:
      desc: Whether to ignore non-existent or empty local repos or fail if one such is encountered.
      current value: true
      default: true
    keep_run_folder:
      desc: whether to keep the run folder with the adapter environment after a run
      current value: false
      default: false
    remote_cache_valid_time:
      desc: Update remote repos if their last checkout was longer ago than this threshold.
      current value: 0
      default: 0
    repos:
      desc: A list of repositories containing frecklets and/or associated resources.
      current value:
      - 'frecklets::gl:frecklets/frecklets-nsbl-default::develop::'
      - 'frecklets::gl:frecklets/frecklets-nsbl-community::develop::'
      - 'roles::gl:frecklets/frecklets-nsbl-default-resources::develop::'
      - 'ansible-tasklists::gl:frecklets/frecklets-nsbl-default-resources::develop::'
      - 'temptings::gl:frecklets/temptings-default::develop::'
      - 'roles::gl:frecklets/frecklets-nsbl-community-resources::develop::'
      - 'ansible-tasklists::gl:frecklets/frecklets-nsbl-community::develop::'
      - user
      - ./.freckles
      default:
      - default
      - user
      - ./.freckles
    run_folder:
      desc: the target for the generated run environment
      current value: /home/markus/.local/share/freckles/runs/archive/run
      default: /home/markus/.local/share/freckles/runs/archive/run

  adapter_config_nsbl

    allow_remote:
      desc: whether to allow remote roles and/or tasklists, can be overwritten by 'allow_remote_roles'
        and 'allow_remote_tasklists'
      current value: false
      default: false
    allow_remote_roles:
      desc: whether to allow remote roles
      current value: n/a
      default: n/a
    allow_remote_tasklists:
      desc: whether to allow remote tasklists
      current value: n/a
      default: n/a
    force_show_log:
      desc: disable the hiding of task details when those contain secret variables, only
        use this for debugging purposes
      current value: false
      default: false

  adapter_run_config_nsbl

    connection_type:
      desc: the connection type, probably 'ssh' or 'local'
      current value: n/a
      default: n/a
    elevated:
      desc: this run needs elevated permissions
      current value: n/a
      default: n/a
    host:
      desc: the host to connect to
      current value: localhost
      default: localhost
    host_ip:
      desc: the host ip, optional
      current value: n/a
      default: n/a
    minimal_facts_only:
      desc: whether to not execute basic box tasks (install python, etc.). Most likely you
        want that set to False.
      current value: false
      default: false
    no_run:
      desc: only create the Ansible environment, don't execute any playbooks
      current value: false
      default: n/a
    output:
      desc: the callback name
      current value: n/a
      default: n/a
    passwordless_sudo:
      desc: the user can do passwordless sudo on the host where those tasks are run
      current value: n/a
      default: n/a
    port:
      desc: the ssh port to connect to in case of a ssh connection
      current value: n/a
      default: 22
    run_callback:
      desc: the output callback to use
      current value: n/a
      default: n/a
    ssh_key:
      desc: the path to a ssh key identity file
      current value: n/a
      default: n/a
    use_ara:
      desc: whether to use ara (https://ara.readthedocs.io)
      current value: false
      default: false
    use_mitogen:
      desc: whether to use mitogen to speed up Ansible playbook execution
      current value: false
      default: false
    user:
      desc: the user name to use for the connection
      current value: n/a
      default: n/a

  adapter_config_tempting

    No configuration.

  adapter_run_config_tempting

    No configuration.

  adapter_config_freckles

    No configuration.

  adapter_run_config_freckles

    No configuration.
```

</div>

</div>

## Using contexts {: .section-title}
<div class="section-block" markdown="1">

To use a context on the command-line, we use the ``-c <context_name>`` option.

### Selecting a single context {: .block-title}
<div class="section-block" markdown="1">

This is the easiest, and most common case. If no context is selected (no ``-c context-name`` option), the default one is used (either the internal default, or, if it exists, the content of the ``$HOME/.config/freckles/default.context`` file). Say we want to use a context that allows us to use the latest
'default' & 'community' frecklets from the 'develop' branch, we can create a 'latest' context file (e.g. by issuing ``freckles context add latest``), and then use it like:

```console
freckles -c latest ...
# or
frecklecute -c latest ...
```

</div>

### Augmenting contexts {: .block-title}
<div class="section-block" markdown="1">

Sometimes we want to change one or two configuration settings for a run but leave the other settings unchanged. For example for debug purposes, or if we want to use the 'result' callback (which produces json we can use in a pipeline). This can be done like so:

```console
freckles -c latest -c keep_run_folder=true -c force_show_log=true ...
```

This will augment the 'latest' context with changed 'keep_run_folder' & 'force_show_log' settings. The order is important. If you would specify ``-c latest`` last, and it had any of the single settings used before it, those would be overwritten.

</div>

### Merging contexts {: .block-title}
<div class="section-block" markdown="1">

Contexts are just basic dictionaries, which is why they can be easily merged. So, similar to augment a single context with single values, you can mix-and-match as many contexts and values as you like. Just be aware that the order, again, is important:

```console
frecklecute -c latest -c callback=result -c dev -c force_show_log=true ...
```

This is an advanced use-case, and you probably will never come across it. Still, it can be useful to know about it, esp. once new features will be added to *freckles*, like for example variable profiles.

</div>

</div>
