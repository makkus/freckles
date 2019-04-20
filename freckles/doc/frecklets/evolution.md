---
title: The evolution of a frecklet
url_path_prio: 100
---

This page describes the different ways to create a *frecklet*. To learn how more about how to call/use those, please check out [this page](/doc/getting_started).


## Supported formats {: .section-title}
<div class="section-block" markdown="1">

A *frecklet* is a text file in either [yaml](https://yaml.org), [json](https://www.json.org), or [toml](https://github.com/toml-lang/toml) format (other formats might be supported later). It can also be, depending on the context it is mentioned, a dict or list data structure. In most cases though it'll be a text file. In the following, we'll exclusively use 'yaml' as our data format.

</div>


## The elastic (non-)schema {: .section-title}
<div class="section-block" markdown="1">

*frecklets* don't have a 'fixed' schema, but offer several ways to express the same thing. This page lists the different ways to describe tasks items and their metadata within a *frecklet*, from the shortest, most minimal way to the most flexible and descriptive.

Offering such a 'non-schema' might be considered fragile and wrong by some (I don't think that to be the case, obviously -- I think it's a worthwhile experiment, and a good trade-off for the read-ability it enables, and the general flexibility it brings to the table). If you don't feel comfortable with this idea but still -- for some reason -- want to use *freckles*, I'd suggest to only use the most verbose way of writing *frecklets* (described at the bottom of this page). It still might make sense to go through all the other options, as it should make it easier to understand how everything works.


### The list of tasks
<div class="section-block" markdown="1">

Without any additional metadata, a *frecklet* is a list of strings and/or dicts.

#### A list of (one or more) strings

In it's most minimal form, a *frecklet* is a text file that contains a list of strings.
Each list item needs to be the name of another frecklet that exists in the current [context](/doc/contexts)
(which can be displayed with ``freckles list``).

Here's an example:
```yaml
- pkg-docker
```

Let's put that into a file called ``my-docker-install.frecklet``. Issuing:
```bash
> frecklecute my-docker-install.frecklet
```
will install *Docker* on the local machine, using [this frecklet](/frecklets/default/virtualization/pkg-docker/).

#### A list of (single-key) dicts

In the example above we don't need any custom variables, as installing Docker is usually pretty straight-forward.

Let's say we want to create a new user, which, as a minimum, requires us to provide a username. We'll use a
readymade and available *frecklet* again (the [``user-exists``](/frecklets/default/system/user-exists/) one), only this time with some custom
parameters (we can investigate the available argument names and what they do with ``freckles frecklet args user-exists``):

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

#### Mixed string(s) and dicts

We can easily mix and match those two types:

```yaml
- user-exists:
    name: markus
- pkg-docker
```

Or, if we want to make sure the newly created user is in the group
that is allowed to user 'docker', we could write (after checking the [``pkg-docker``](/frecklets/default/virtualization/pkg-docker/) documentation):

```yaml
- user-exists:
    name: markus
- pkg-docker:
    users:
      - markus

```
</div>

### Metadata
<div class="section-block" markdown="1">

Once we want to add metadata, a *frecklet* becomes a dict-like data structure. The task-list we used so far moves to a key called ``frecklets``.

Additional allowed keys are: ``doc``, ``args``, and ``meta``.

#### Adding documentation

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
  short_help: Creates the user 'markus' with the uid 1010.
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
> frecklecute my-create-user.frecklet --help
Usage: frecklecute my-create-user.frecklet
           [OPTIONS]

  This uses the 'create-user' frecklet to create a
  single user, named 'markus'.

  The UID of this user will be '1010'.
```

#### Adding arguments

Up until now, our *frecklet* is hardcoded to do exactly one thing, creating a user with a fixed name and UID. What if we want to re-use it with different values? This is what variables are, and what arguemnts are used for in command-line tools.

##### Non-typed arguments

If you don't want to clutter your *frecklet* with metadata about its argument(s), and you are happy for them to be required, non-empty strings, all you have to do is use a special template syntax ( ``{{:: key ::}}`` ) for the values you want user input for:

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

!!! note
    Internally, *freckles* uses the [Cerberus](https://docs.python-cerberus.org) and [Click](https://click.pocoo.org/) Python libraries to validate the arguments, as well as create the command-line interface for ``frecklecute``. The configuration under the ``args`` key is forwared more or less unchanged to those libraries (details [here](https://TODO)), so please peruse their respective documentation for details if necessary.

Note how we use ``required: no`` for our ``uid`` value. This is a good way to specify optional arguments. If a 'none' value or empty string is passed to a key in a dict, it won't be forwarded to the child *frecklet* that is called. Also, we have specified the type of the argument as an integer under ``args``. This causes the variable to be validated, and if successful, converted into the proper type.

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

</div>

</div>
<!-- end section non-schema -->
