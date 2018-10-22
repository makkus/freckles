# the evolution of a *frecklet*

## a list of strings

In it's most basic form, a *frecklet* is a text file that contains a list of strings in ``yaml`` format.
Each list item needs to be the name of another frecklet that exists in the current [context](https://freckles.io/TODO)
(which can be displayed with ``freckfreckfreck frecklet list``).

Here's an example:
```yaml
- install-docker
```

Let's put that into a file called ``my-docker-install.frecklet``. Issuing:
```bash
frecklecute my-docker-install.frecklet
```
will install *Docker* on the local machine.

## a list of (single-key) dicts

In the example above we don't need any custom variables, as installing Docker is usually pretty straight-forward.

Let's say we want to create a new user, which, as a minimum, requires us to provide a username. We'll use a
readymade and available *frecklet* again (the [``create-user``](https://gitlab.com/freckles-io/frecklets-nsbl/blob/develop/system/users/create-user.frecklet) one), only this time with some custom
vars (we can investigate the available variable names with ``TODO``):

```yaml
- create-user:
    name: markus
```
or, if we also want to specify the users UID:
```yaml
- create-user:
    name: markus
    uid: 1010
```

In both cases, after putting the content in a file (say, ``my-create-user.frecklet``), we can create
the user (or rather: make sure the user exists) with a simple:

```bash
frecklecute my-create-user.frecklet
```

## including documentation

Having documentatin is always good, and the best place for documentation to live is very close to
the thing it documents. If we want to add documentation to a *frecklet*, we need to transform our
 frecklet content into a dictionary, and move the current tasklist (well, list of a single task in our case)
 under the ``tasks`` key:

```yaml
tasks:
  - create-user:
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

tasks:
  - create-user:
      name: markus
      uid: 1010
```

Now, if we use the ``--help`` flag with ``frecklecute`` we'll see this:

```
$ frecklecute my-create-user.frecklet --help
Usage: frecklecute my-create-user.frecklet
           [OPTIONS]

  This uses the 'create-user' frecklet to create a
  single user, named 'markus'.

  The UID of this user will be '1010'.
```

## adding arguments

Up until now, our *frecklet* is hardcoded to do exactly one thing, creating a user with a fixed name and UID. What if we want to re-use it with different values? This is what arguments are used for in command-line tools, and this is what we'll use as well.

### non-typed arguments

If you don't want to clutter your *frecklet* with metadata about its argument(s), and you are happy to receive strings, all you have to do is use a special template syntax ( ``{{:: key ::}}`` ) for the values you want user input for:

``` yaml
tasks:
  - create-user:
      name: "{{:: username ::}}"
      uid: 1010
```

This will tell *freckles* to convert the ``{{:: username ::}}`` string into a (required) commandline option, and use the user input for it as the value:

```
$ frecklecute my-create-user.frecklet --help
Usage: frecklecute create-user.frecklet
           [OPTIONS]

  n/a

Options:
  --username TEXT  n/a  [required]
  --help           Show this message and exit.

$ frecklecute my-create-user.frecklet
Usage: frecklecute create-user.frecklet [OPTIONS]

Error: Missing option "--username".
```

This is how we run this minimal *frecklet* now:

``` yaml
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
Note how *frecklecute* (rather, the underlying ``ansible-playbook`` command) asks for the ``sudo`` password automatically (it won't do that if you have passwordless sudo configured for whoever is executing the command). This is usually needed to create a user.

Also want to ask the user for the UID? Sure:

``` yaml
tasks:
  - create-user:
      name: "{{:: username ::}}"
      uid: "{{:: uid ::}}"
```

Unfortunately, that won't work, as the ``create-user`` *frecklet* expects an integer, not a string:

```
➜ frecklecute my-create-user.frecklet --username markus --uid 1011

error: Invalid or missing argument 'uid': '1011' => {'uid': ['must be of integer type']}
```

Not to worry though, that's what [Jinja2 filters](http://jinja.pocoo.org/docs/2.10/templates/#filters) are for:

``` yaml
tasks:
  - create-user:
      name: "{{:: username ::}}"
      uid: "{{:: uid | int ::}}"
```

This will now work. For a full list of available filters, check [here](https://TODO).

### typed arguments

Using non-typed arguments is a quick and easy way to create *frecklets* that take user input, and it's well suited for
easy *frecklets* you want to create quickly. It keeps the content of the *frecklet* neat and tidy, and you can see instantly what it is supposed to do.

For more involved *frecklets* it is recommended to specify (and document) your arguments though. Similar to how the ``doc`` key works, every *frecklet* can also have a *args* key. Here's an example for our ``my-create-user.frecklet``:

``` yaml
args:
  username:
    type: string
    required: yes
    doc:
      short_help: the name of the new user
  uid:
    type: integer
    required: no
    doc:
      short_help: the uid of the new user

tasks:
  - create-user:
      name: "{{:: username ::}}"
      uid: "{{:: uid | default(omit) ::}}"
```

Every variable we want to ask the user needs to be present as key under the ``args`` section, and also at least once somewhere in ``tasks``. If the former is not the case, *freckles* will use a default argument spec (a required string). If the latter is not the case, *freckles* will just ignore it.

Note how we use ``required: no`` for our ``uid`` value, combined with the ``.. | default(omit)`` filter in the ``tasks`` section. This is a good way to specify optional arguments. Also, we don't need the ``int`` filter anymore, as we have specified the type of the argument under ``args``.

Let's see what ``frecklecute`` makes of this:

```
$ frecklecute my-create-user.frecklet --help
Usage: frecklecute my-create-user.frecklet
           [OPTIONS]

  n/a

Options:
  --username TEXT  the name of the new user  [required]
  --uid INTEGER    the uid of the new user
  --help           Show this message and exit.
```

And that's basically it. There are more details you can adjust, both in terms how the *frecklet* presents itself to
its users, and in terms of specifying exactly which tasks to execute, and in which manner. For more details on those,
please refer to the [*freckles* documetation](https://docs.freckles.io).
