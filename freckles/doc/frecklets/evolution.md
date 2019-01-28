---
title: The evolution of a frecklet
url_path_prio: 100
---

This page lists the different ways to describe tasks items and their metadata within a *frecklet*. From the shortest, most minimal way to the most flexible and descriptive.

Offering such a 'non-schema' might be considered fragile and wrong by some (I don't think that is the case, obvoulsly -- I think it's a worthwhile trade-off for the read-ability it brings). If you think so, I'd suggest to only use the moste verbose way (described at the bottom of this page) of writing a *frecklet*. It still might make sense to go through all the other options, as it should make it easier to understand what this is all about.

For the purpose of illustrating how to describe tasks, we will only call pre-made *frecklets* from [this list](/frecklet-index)), not any connector-specific task descriptions. To learn how to use those, please check out [this page](https://TODO).

## The list of tasks

### A list of (one or more) strings

In it's most basic form, a *frecklet* is a text file that contains a list of strings in ``yaml`` format.
Each list item needs to be the name of another frecklet that exists in the current [context](https://freckles.io/TODO)
(which can be displayed with ``frecklecute --help-all``).

Here's an example:
```yaml
- pkg-docker-installed
```

Let's put that into a file called ``my-docker-install.frecklet``. Issuing:
```bash
frecklecute my-docker-install.frecklet
```
will install *Docker* on the local machine, using [this frecklet](/frecklet-index/default/pkg-docker-installed/).

### A list of (single-key) dicts

In the example above we don't need any custom variables, as installing Docker is usually pretty straight-forward.

Let's say we want to create a new user, which, as a minimum, requires us to provide a username. We'll use a
readymade and available *frecklet* again (the [``user-exists``](/frecklet-index/default/user-exists) one), only this time with some custom
vars (we can investigate the available variable names and what they do with ``freckfreckfreck frecklet vars user-exists``):

```yaml
- user-exists:
    name: markus
```
or, if we also want to specify the users UID:
```yaml
- user-exists:
    name: markus
    uid: 1010
```

In both cases, after putting the content in a file (say, ``my-create-user.frecklet``), we can create
the user (or rather: make sure the user exists) with a simple:

```console
frecklecute my-create-user.frecklet
```

### Mixed string(s) and dicts

We can easily mix and match those two types:

```yaml
- user-exists:
    name: markus
- pkg-docker-installed
```

``frecklecute`` will execute them in order.

## Adding documentation

Having documentatin is always good, and the best place for documentation to live is very close to
the thing it is documenting. If we want to add documentation to a *frecklet*, we need to transform our
 frecklet content into a dictionary, and move the current tasklist (well, list of a single task in the example below)
 under the ``frecklets`` key:

```yaml
frecklets:
  - user-exists:
      name: markus
      uid: 1010
```
This is equivalent to the list-version of the *frecklet* from the example above. Now, for some documentation:

```yaml
doc:
  short_help: creates the user 'markus' with the uid 1010
  help: |
    This uses the 'create-user' frecklet to create
    a single user, named 'markus'.

    The UID of this user will be '1010'.

frecklets:
  - user-exists:
      name: markus
      uid: 1010
```

This information can be used by the *freckles* framework, and displayed where necessary. For example, the ``frecklecute`` application can use it to construct a command-line help text:

```console
$ frecklecute my-create-user.frecklet --help
Usage: frecklecute my-create-user.frecklet
           [OPTIONS]

  This uses the 'create-user' frecklet to create a
  single user, named 'markus'.

  The UID of this user will be '1010'.
```

It is also used to render the *frecklet* documentation on the child pages of [the frecklet index](/frecklet-index).

## Adding arguments

Up until now, our *frecklet* is hardcoded to do exactly one thing, creating a user with a fixed name and UID. What if we want to re-use it with different values? This is what variables are, and what arguemnts are used for in command-line tools.

### Non-typed arguments

If you don't want to clutter your *frecklet* with metadata about its argument(s), and you are happy to receive strings, all you have to do is use a special template syntax ( ``{{:: key ::}}`` ) for the values you want user input for:

``` yaml
frecklets:
  - user-exists:
      name: "{{:: username ::}}"
      uid: 1010
```

This will tell *freckles* to convert the ``{{:: username ::}}`` string into a (required) commandline option, and use the user input for it as the variable value:

```console
$ frecklecute my-create-user.frecklet --help
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
$ frecklecute my-create-user.frecklet --username markus

SUDO password: xxxxx

╭─ starting: 'my-create-user'
├╼ connector: nsbl
│  ├╼ host: localhost
│  │  ├╼ starting playbook
│  │  │  ├╼ doing freckly init stuff, may take a while
│  │  │  │  ╰╼ ok
│  │  │  ├╼ creating user if it doesn't exist yet: markus
│  │  │  │  ╰╼ ok
│  │  │  ╰╼ ok
│  │  ╰╼ ok
│  ╰╼ ok
╰─ ok
```

!!! note

    Notice how *frecklecute* (rather, the underlying ``ansible-playbook`` command) asks for the ``sudo`` password automatically (it won't do that if you have passwordless sudo configured for whoever is executing the command). This is usually needed to create a user.

Maybe we also want to ask for the UID? Sure:

``` yaml
frecklets:
  - user-exists:
      name: "{{:: username ::}}"
      uid: "{{:: uid ::}}"
```

Execute ``frecklecute my-create-user --help`` again to see the newly created cli help.

### Typed arguments

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

!!! note
    Internally, *freckles* uses the [Cerberus](https://docs.python-cerberus.org) and [Click](https://click.pocoo.org/) Python libraries to validate the arguments, as well as create the command-line interface for ``frecklecute``. The configuration is forwarded under the ``args`` key is forwared more or less unchanged (details [here](https://TODO)) to them, so please peruse their respective documentation for details if necessary.

Note how we use ``required: no`` for our ``uid`` value. This is a good way to specify optional arguments. If a 'none' value is passed to a key in a dict, it won't be forwarded to the child *frecklet* that is called. Also, we have specified the type of the argument as an integer under ``args``. This causes the variable to be validated, and if successful, converted into the proper type.

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
please refer to the [*freckles* documetation](https://docs.freckles.io).
