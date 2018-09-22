# the evolution of a *frecklet*

## list of strings

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

## list of (single-key) dicts

In the example above we don't need any custom variables, as installing Docker is usually pretty straight-forward.

Let's say we want to create a new user, which, as a minimum, requires us to provide a username. We'll use a
readymade and available *frecklet* again (the ``ensure-user-exists`` one), only this time with some custom
vars (we can investigate the available variable names with ``TODO``):

```yaml
- ensure-user-exists:
    name: markus
```
or, if we also want to specify the users UID:
```yaml
- ensure-user-exists:
    name: markus
    uid: 1010
```

In both cases, after putting the content in a file (say, ``my-create-user.frecklet``), we can create
the user (or rather: make sure the user exists) with a simple:

```bash
frecklecute my-create-user.frecklet
```

## adding documentation

Having documentatin is always good, and the best place for documentation to live is very close to
the thing it documents. If we want to add documentation to a *frecklet*, we need to transform our
 frecklet content into a dictionary, and move the current tasklist (well, list of a single task in our case)
 under the ``tasks`` key:

```yaml
tasks:
  - ensure-user-exists:
      name: markus
      uid: 1010
```
This is equivalent to the list-version of the *frecklet* from the example above. Now, for some documentation:

```yaml
doc:
  short_help: creates the user 'markus' with the uid 1010
  help: |
    This uses the 'ensure-user-exists' frecklet to create a single user, named 'markus'.

    The UID of this user will be '1010'.
```

Now, if we use the ``--help`` flag with ``frecklecute`` we'll see this:

```
$ frecklecute my-create-user.frecklet --help
Usage: frecklecute my-create-user.frecklet
           [OPTIONS]

  This uses the 'ensure-user-exists' frecklet to create a
  single user, named 'markus'.

  The UID of this user will be '1010'.
```
