---
title: The evolution of a frecklet
url_path_prio: 100
---

This page describes the different ways to create a *frecklet*. To learn how more about how to call/use those, please check out [this page](/doc/getting_started).

To get into detail about all the properties and allowed keys/values of a full-blown *frecklet*, read the [Anatomy of a *frecklet*](/doc/frecklets/anatomy) page.


## Supported formats {: .section-title}
<div class="section-block" markdown="1">

A *frecklet* is a text file in either [yaml](https://yaml.org), [json](https://www.json.org), or [toml](https://github.com/toml-lang/toml) format (other formats might be supported later). It can also be, depending on the context (e.g. when using *freckles* as a Python library) a dict or list data structure. In most cases though it'll be a text file. In the following, we'll exclusively use 'yaml' as our data format.

</div>


## The elastic (non-)schema {: .section-title}
<div class="section-block" markdown="1">

*frecklets* don't have to follow a 'fixed' schema; they can 'mature' as they become more important. The *freckles* parser allows for several ways to express the same thing so the complexity of your code can mirror the importance of the context it is executed in. This page lists the different ways to describe tasks items and their metadata within a *frecklet*, from the shortest, most minimal way to the most powerful and descriptive.

Offering such a 'non-schema' might be considered fragile and wrong by some (I don't think that to be the case, obviously -- I think it's a worthwhile experiment, and a good trade-off for the read-ability it enables, and the general flexibility it brings to the table). If you don't feel comfortable with this idea but still -- for some reason -- want to use *freckles*, I'd suggest to only use the most verbose way of writing *frecklets* (described at the bottom of this page). It still might make sense to go through all the other options, as it should make it easier to understand how everything works.


### The list of tasks
<div class="section-block" markdown="1">

Without any additional metadata, a minimal *frecklet* is just a list of strings and/or dicts.

#### A list of (one or more) strings

In it's most basic form, a *frecklet* is a text file that contains a list of strings where each string represents a command (a.k.a. other *frecklet*) that does not require any arguments.
Each list item needs to be the name of another frecklet that exists in the current [context](/doc/configuration)
(get a list of all possible ones with: ``freckles list``).

Here's an example:
```yaml
- docker-service
```

Let's put that into a file called ``my-docker-install.frecklet``. Issuing:
```bash
> frecklecute my-docker-install.frecklet
```
would install *Docker* on the local machine (by executing [this frecklet](/frecklets/default/virtualization/docker-service/)).

#### A list of single-key dicts

In the example above we don't need any custom variables, as installing Docker is usually pretty straight-forward, and there is no configuration option that requires user input. This uses a list of single-key dicts, a data structure you'll see often within *freckles* as it's quite easy for a human to grasp what it is meant to express (esp. in 'yaml' format).

Let's say we want to create a new user, which -- obviously -- as a minimum requires us to provide a username. We'll use a
ready-made and available *frecklet* again (the [``user-exists``](/frecklets/default/system/user-exists/) one), only this time with some custom
parameters (we can investigate the available argument names and what they do with either ``freckles frecklet args user-exists`` or ``frecklecute user-exists --help``):

```yaml
- user-exists:
    name: markus
```

or, if we also want to specify the users' UID:

```yaml
- user-exists:
    name: markus
    uid: 1010
```

In both cases, after putting the content in a file (say, ``my-new-user.frecklet``), we can create
the user (or rather: make sure the user exists) with a simple:

```console
frecklecute my-new-user.frecklet
```

#### Mixed string(s) and dicts

We can easily mix and match those two types:

```yaml
- user-exists:
    name: markus
- docker-service
```

Or, if we want to make sure the newly created user with a specific id is in the group
that is allowed to user 'docker', we could write (after checking the [``docker-service``](/frecklets/default/virtualization/docker-service/) documentation):

```yaml
- user-exists:
    name: markus
    uid: 1010
- docker-service:
    users:
      - markus

```

Note: if we didn't need the custom ``uid`` for our user, the ``docker-service`` user would have created the user automatically, and ``user-exists`` would not have been necessary.


#### Single-and double-key dictionaries

The (single-key dicts) example from above can also be expressed as a list of dicts in a slightly different format:

```yaml
- frecklet: user-exists
  vars:
    name: markus
- frecklet: docker-service
  vars:
    users:
      - markus
```

This by itself is not useful, as it's just a more verbose, and less readable way of saying the same thing. It makes more
sense once we add another keyword though: ``target`` (as in the ``--target`` option of the ``frecklecute`` command).

This enables us to have tasks that are executed on different targets, in the same *frecklet*. By default, a *frecklet* executes on the target
that is specified on the commandline with ``--target``, or, if that is not used, 'localhost'. Having 'target'  in the *frecklet*
will override both options. Here's how that would look:

```yaml
- frecklet: file-with-content
  vars:
    path: /tmp/install.log
    content: |
      Installed Docker on host 'dev.frkl.io'.
- frecklet: docker-service
  target: admin@dev.frkl.io
  vars:
    users:
      - markus
```

This example is a bit nonsensical, but where this comes in really handy, for example, is when you want to provision a
new VM from a cloud provider. The first task would be executed locally, and talk to the providers API to create a new VM.
The second one would connect to that VM (probably as root), and does some initial setup (like provisioning an admin user, disabling password-login for ssh, etc.).

There is a further evolution step to double-key dictionary *frecklet*-items. This is only usable in advanced use-cases,
so we'll ignore that for now, and come back to it later, at the end of the page. For now, le'ts look into metadata to
improve our *frecklets* usability (and usefulness).

</div>
<!-- end list of tasks -->

### The metadata dictionary
<div class="section-block" markdown="1">

*frecklets* like the ones we discussed so far are really quick to create, they are good for prototyping, and serve as easy-to-understand starting points for more complex tasks. Once you get to a stage where you want to share a *frecklet*, or maybe use it in production, I'd recommend adding some metadata though. There are different types of metadata you can add:

- Documentation (``doc`` keyword)
- Arguments (``args`` keyword)
- Generic metadata, to be used in plugins or for other purposes (``meta`` keyword, which we'll ignore for now)

Once we want to add metadata, a *frecklet* becomes a dict-like data structure. The task-list we used so far moves to a key called ``frecklets``.

#### Adding documentation

Having documentation is always good, and the best place for documentation to live is very close to
the thing it is documenting. If we want to add documentation to a *frecklet*, we need to transform our
 frecklet content into a dictionary, and move the current task-list (well, list of a single task in the example below)
 under the ``frecklets`` key:

```yaml
frecklets:
  - user-exists:
      name: markus
      uid: 1010
```
This is a valid *frecklet*, and it is equivalent to the 'pure-list'-version with the same content from a few examples before. Now, for some documentation:

```yaml
doc:
  short_help: Creates the user 'markus' with the uid 1010.
  help: |
    Creates a single user, named 'markus'.

    The UID of this user will be '1010'.

frecklets:
  - user-exists:
      name: markus
      uid: 1010
```

This information can be used by the *freckles* framework, and displayed where necessary. For example, the ``frecklecute`` application can use it to construct a command-line help text:

```console
> frecklecute my-create-user.frecklet --help
Usage: frecklecute my-create-user.frecklet
           [OPTIONS]

  Creates a single user, named 'markus'.

  The UID of this user will be '1010'.
```

#### Adding arguments

Up until now, our *frecklet* is hardcoded to do exactly one thing, creating a user with a fixed name and UID. What if we want to re-use it with different values? This is a typical use-case for variables, and what arguments are used for in command-line tools.

##### Non-typed arguments

If you don't want to clutter your *frecklet* with metadata about its argument(s), and you are happy for them to be required and non-empty strings, all you have to do is use a special *freckles* template syntax ( ``{{:: key ::}}`` ) for the values you want user input for:

``` yaml
frecklets:
  - user-exists:
      name: "{{:: username ::}}"
      uid: 1010
```

This will tell *freckles* to convert the ``{{:: username ::}}`` string into a (required) commandline option, and use the user input for it as the variable value:

```console
> frecklecute my-create-user.frecklet --help
Usage: frecklecute create-user.frecklet
           [OPTIONS]

  n/a

Options:
  --username TEXT  n/a  [required]
  --help           Show this message and exit.

$ frecklecute my-create-user.frecklet
Usage: frecklecute my-create-user.frecklet [OPTIONS]

Error: Missing option "--username".
```

This is how we run this minimal *frecklet* now:

``` console
> frecklecute --ask-sudo-pass my-create-user.frecklet --username admin

SUDO PASS:

╭╼ starting run
│  ├╼ running frecklet: /home/markus/my-create-user.frecklet (on: localhost)
│  │  ├╼ starting Ansible run
│  │  │  ├╼ remove cached sudo credential
│  │  │  │  ╰╼ ok
│  │  │  ├╼ ensure user 'admin' exists
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰╼ ok

```

Maybe we also want to ask for the UID? Sure:

``` yaml
frecklets:
  - user-exists:
      name: "{{:: username ::}}"
      uid: "{{:: uid ::}}"
```

Execute ``frecklecute my-create-user --help`` again to see the newly created cli help.

##### Typed arguments

Using non-typed arguments is a quick and easy way to create *frecklets* that take user input, and it's well suited for
simple task-lists you want to create quickly. It keeps the content of the *frecklet* neat and tidy, and you can see instantly what it is supposed to do.

For more involved *frecklets* it is recommended to specify (and document) your arguments though. Similar to how the ``doc`` key works, every *frecklet* can also have an *args* key. Here's an example for our ``my-create-user.frecklet``:

```yaml
args:
  username:
    type: string
    required: yes
    empty: no
    doc:
      short_help: the name of the new user
  uid:
    type: integer
    required: no
    doc:
      short_help: the uid of the new user

frecklets:
  - [user-exists](https://freckles.sh):
      name: "{{:: username ::}}"
      uid: "{{:: uid ::}}"
```

Every variable we want to ask the user needs to be present as key under the ``args`` section, and also at least once somewhere in ``frecklets``. If the former is not the case, *freckles* will use a default argument spec (a required item, non-empty). If the latter is not the case, *freckles* will just ignore it.

---

**Note**:

Internally, *freckles* uses the [Cerberus](https://docs.python-cerberus.org) and [Click](https://click.palletsprojects.com) Python libraries to validate the arguments, as well as create the command-line interface for ``frecklecute``. The configuration under the ``args`` key is forwarded more or less unchanged to those libraries (details [here](https://TODO)), so please peruse their respective documentation for details if necessary.

---  

Notice how we use ``required: no`` for our ``uid`` value. This is a good way to specify optional arguments. If a 'none' value or empty string is passed to a key in a dict, it won't be forwarded to the child *frecklet* that is called. Also, we have specified the type of the argument as an integer under ``args``. This causes the variable to be validated, and if successful, converted into the proper type.

Let's see what ``frecklecute`` makes of this:

```console
$ frecklecute my-create-user.frecklet --help
Usage: frecklecute my-create-user.frecklet
           [OPTIONS]

  n/a

Options:
  --username TEXT  the name of the new user  [required]
  --uid INTEGER    the uid of the new user
  --help           Show this message and exit.
```

What happens if we provide a non-integer value for ``uid``? Let's see:

```console
$ frecklecute my-create-user.frecklet --username markus --uid markus
Usage: frecklecute my-create-user.frecklet [OPTIONS]
Try "frecklecute my-create-user.frecklet --help" for help.

Error: Invalid value for "--uid": markus is not a valid integer
```

And that's basically it. There are more details you can adjust, both in terms how the *frecklet* presents itself to
its users, and in terms of specifying exactly which tasks to execute, and in which manner. For more details on those,
please refer to the [*freckles* documentation](https://freckles.io/doc).

</div>
<!-- end metadata dictionary -->

### Exploded ``frecklet``-items
<div class="section-block" markdown="1">

As I've mentioned before, there is an additional evolutionary step to how the items in the list under ``frecklets`` can
be expressed. This is the internal representation of such an item within *freckles*, and it offers the most flexibility,
but trades in some readability and ease of use. We'll only give a broad overview of the topic here, for more in-detail
information please refer to the [Anatomy of a *frecklet*](/doc/frecklets/anatomy) page.

For the purpose of explaining this, we'll use a *frecklet* without metadata, and only one task. This format is really
only useful to develop new *frecklets* that call low-level tasks that don't have their own *frecklet* yet. Ideally, end-users
would only ever have to deal with pre-developed *frecklets*, but once requirements become more complex, chances increase
that some custom development needs to be done.

Ok, here's the *frecklet* we'll be working with:

```yaml
# filename: example.frecklet
- user-exists:
    name: markus
```

Very simple, one task, makes sure a user exists on a system. You can use *freckles* to display the fully-exploded,
internally used data structure of a *frecklet*. Here's how:

```console
> freckles frecklet explode example.frecklet

doc: {}

args: {}

frecklets:

  - frecklet:
      name: user-exists
      type: frecklet
    task:
      command: user-exists
    vars:
      name: markus
```

The important part is the one list item under the ``frecklets`` key. We can see the item is a directory with 3 keys:

- ``frecklet``: contains general metadata about the frecklet item and it's type
- ``task``: contains [adapter](/doc/adapters)-specific metadata (in this case that does not really apply, as the item is just another *frecklet*)
- ``vars``: the vars to use for this *frecklet* in this run

As I've said, using this format just to call an existing *frecklet* does not make too much sense. Let's see how the ``user-exists`` frecklet is implemented internally. Apart from creating the users group if it does not exist and some optional metadata (which we'll both ignore here), this is the basic implementation of ``user-exists``:

```yaml
frecklets:
  - frecklet:
      name: user
      type: ansible-module
      msg: "ensure user '{{:: name ::}}' exists"
    task:
      become: true
    vars:
      name: "{{:: name ::}}"
      state: present
      groups: "{{:: group ::}}"
      append: true
      uid: "{{:: uid ::}}"
      system: "{{:: system_user ::}}"
      password: "{{:: password | sha512_crypt ::}}"
      shell: "{{:: shell ::}}"
```

You could put this into a file and call it with ``frecklecute <filename> --help``, and you'd get a basic help message, similar to the one we saw above, with all of the arguments being required (and strings).

The 'vars' value works like in any of the other examples we've looked at so far, so I'll not go into that again here. The interesting stuff happens in ``frecklet``, and ``task``.

#### The ``frecklet`` (sub-)key

The important key in this part of the configuration is ``type``. This lets *freckles* know which one of the available [freckles adapters](/doc/adapters) to use to process this item. Every adapter registers with *freckles* with a list of supported types. In this case (``ansible-module``) the [nsbl](/doc/adapters/nsbl) one will be used.

There are other keys you can put into ``frecklet``, the most important one being ``skip``, which lets you skip a task in certain situations. Here we are also showing ``msg``, which is the message the user sees when this task is executed.  

#### The ``task`` (sub)-key

This one lets you fine-tune the behaviour of this (dynamically created) *frecklet* in question. In this case, the [``user``](http://docs.ansible.com/ansible/latest/user_module.html) Ansible module will be called with the ``become`` key set to ``true``.

The content of this sub-key is highly dependent on the adapter used, so you'll have to refer to the documentation of the adapter in question for details.

That's all folks. Check out the other docs, or head over to the [friends of freckles](https://friends.of.freckles.io) if you have questions!

</div>
<!-- end fully flexible -->

</div>
<!-- end section non-schema -->
