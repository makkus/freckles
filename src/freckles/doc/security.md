---
title: Security
url_path_prio: 200
draft: false
---

Security is an important topic, even more so when sudo/root permissions are involved.

I don't think I'll be able to do the topic justice here, there are just too many variables and scenarios to take into account. I'll try my best though. So, on this page I'll list all the security-relevant patterns and strategies that *freckles* uses, and, if possible, point out options you have, and their implications.

If you encounter any seucrity-related questions or issues that are not mentioned here, please visit the [Security](https://friends.of.freckles.io/c/security) category on the [friends of freckles](https://friends.of.freckles.io) forum, and create a topic.

Make sure you use *freckles* carefully, it is a powerful tool, and those usually come with a 'shoot-yourself-in-the-foot'-button. Make sure you know where that is, and try to stay away from that general area...

### Root permissions {: .section-title}
<div class="section-block" markdown="1">

Quite deliberately, *freckles* will never require any sudo/root permissions when installed or run by itself. It will only ask you for a sudo password
when you tell it to run tasks that require them. So, there is never a need to do something like:

```console
sudo freckles ...
```

*freckles* has internal smarts to figure out whether it needs to ask for a 'sudo' password, here's how that goes:

- check if the *frecklet* needs elevated permissions at all
    - if no elevated permissions are needed, don't do any further checks
- check if the '--ask-become-pass' flag is set
    - if it is, ask for the password and use that in the run
- check if the target is local or remote
- if remote:
    - assume the login user will have password-less sudo access (or is 'root', in which case the question is moot)
- if local:
    - check the username in the 'target' variable
        - if the user in the target variable is the same as the one running *freckles*
            - check if the current user can do 'passwordless sudo'
                - if it can, do no further check and use that to get elevated privileges whenever necessary
            - if it can't do passwordless sudo, ask for the users password and use that down the line (if the user does not have sudo permissions at all, the run will fail eventually)
        - if the user in the target var is different than the one running *freckles*
            - use/change 'ssh' as connection type instead of 'local'
            - assume the login user will have password-less sudo access (or is 'root', in which case the question is moot)

So, what this means in practice is that if you have a task that requires elevated permissions, and the task runs locally as the same user that runs *freckles* ('-t localhost', or no '-t' flat at all), , *freckles* will do the right thing, and will only ask for a password if necessary.

If you run a task with a remote target, you have to specify the '--ask-become-pass' flag in the cases where the remote user (the 'user' part in '-t user@target.com') can't do password-less sudo (but has sudo permissions in general -- if it has not, the task will fail at some point).

</div>

### Installation {: .section-title}
<div class="section-block" markdown="1">

#### The bootstrap script {: .block-title}
<div class="section-block" markdown="1">

The *freckles* application is a single binary, and can be downloaded and placed anywhere on the filesystem. It is usually a good idea
to put it in a folder that is in your sessions [``PATH``](https://www.cs.purdue.edu/homes/bb/cs348/www-S08/unix_path.html).

You can either download *freckles* manually, or use [freck](https://gitlab.com/freckles-io/freck), the *freckles bootstrap script*, to do it for you.

'Curly bootstrap scripts' like the *freck* are sometimes frowned upon as being inherently less secure than any alternatives. I don't think
that is actually true in a lot of cases, but if you don't want to take any chances, just do everything manually and don't think about it.

In my mind, if you trust somebody enough to run their application, you might as well trust the bootstrap script they provide, esp. if it is hosted from the same location.

In the case of *freckles*, the one advantage manually downloading the binary to using the bootstrap script I can see is that the bootstrap script
could have been modified by a 3rd party. But, if that 3rd party has access to the bootstrap script, they would most likely also have had access to the binary or potentially the build process, so there is really not much gained here.

The script itself offers some neat features, first and foremost it lets you execute *freckles* straight away, within the same invocation you use to download it. It also, optionally, can delete *freckles* and any intermediate files that were created during a run after the run finishes. This is really convenient for one-off provisioning runs, or when building Docker images.

If you use *freck* a lot, I'd recommend you host the script yourself, and maybe also the *freckles* binary. It is not finished yet, but I'm working on a *frecklet* that can setup a web-server to host *freckles* and a customizable bootstrap script, as well as your *frecklet* repositories. This will allow for you to tailor everything to your environment and requirements. Stay tuned, and ping me if that interests you.

</div>

#### Binary signing {: .block-title}
<div class="section-block" markdown="1">

Currently, only the Mac binary of *freckles* is signed. The plan is to also sign the Linux binary, or at least provide hashes, but public opinion seems to be
split on whether that really provides any advantage over just serving the binaries via https. I'm not really sure myself, so I'd be happy to get some input if you have some.

</div>
</div>

### Running *freckles* {: .section-title}
<div class="section-block" markdown="1">

As was mentioned above, *freckles* only asks you for sudo/root passwords when the task you want it to execute requires it. Sometimes *freckles* will be
run as the root user, for example when run inside a Docker build process. Sometimes a system is setup so that there exists an admin user who has
access to sudo without having to provide a password. In fact, *freckles* comes with [a *frecklet*](/frecklets/system/passwordless-sudo-users) to setup just that.

The only 'real' advice I can give without knowing any further details: try to run *freckles* always with the minimum amount of privileges that are needed for a certain task.

#### 'Trusted' *frecklets* {: .block-title}
<div class="section-block" markdown="1">

To somewhat mitigate users using harmful *frecklets*, *freckles* comes with two 'officially sanctioned' sets of *frecklets*. Those come with their own sort of 'trust levels'. The items from the [default](/frecklets/default) repository are vetted by the *freckles* developer himself (aka, me), so if you trust *freckles*, can also trust those. The [community](/frecklets/community) *frecklet* repository is created and curated by the community. There will hopefully be a lot of eyes on the contents of the *frecklets* in there, which will make it harder for somebody to sneak in something malicious.

</div>

#### Remote repo permission config {: .block-title}
<div class="section-block" markdown="1">

Related to the above, by default *freckles* does not allow any outside *frecklets* to be run, it does not even allow you to change the configuration to allow them, unless you [unlock the configuration](/configuration/contexts) first.

After that, you can add repositories to the 'allow_remote_whitelist', or set the 'allow_remote' configuration value to 'true'. Again, this is your own decision, and you should make an informed one. If you host your own repositories of *frecklets*, please include a Readme pointing out those issues, and maybe put a link to here in it.

</div>
</div>

### Password entry {: .section-title}
<div class="section-block" markdown="1">

Some *frecklets* need passwords as user input. This is a difficult thing to do securely. *freckles* still misses a few features that will make handling
passwords better, easier, and more secure. In the future there will be integration to password stores (e.g. Hashicorp Vault, Bitlocker, the OS keychain, ...). For now, there are only a few (more basic) options, so it's a good idea you know about them, and can pick the best one for your scenario.

When writing a *frecklet*, you can mark arguments ``secret``, which will tell *freckles* to handle them differently to 'normal' ones. It looks like this:

```yaml
args:
  db_password:
    doc: The password for the database.
    type: string
    required: true
    secret: true
  other_arg:
    doc: ...
```

All the *frecklets* in the 'default' and 'community' repositories use this marker. If you use a *frecklet* from a 3rd party, have a look at it's content and make sure this is done properly. This is probably also a good indicator on the quality of the *frecklet* in question...

#### Plain password via command-line arg {: .block-title}
<div class="section-block" markdown="1">

It is not a good idea to just use passwords as normal cli arguments, ala:

```console
frecklecute user-exists --password password123 markus
```

Even though *freckles* will internally handle this value in a secure manner, this command will show up in your shell history file (including the password string), so you should prefer to never do that.

</div>

#### Using the '--vars' arg {: .block-title}
<div class="section-block" markdown="1">

One option you have is to store your key/password pair in a yaml (or json/toml) file, and make this file readable only by your user (``chmod 0700 vars_file.yml``). Then use the ``--vars var_file`` command-line argument of *freckles* and point to that file.

This is by no means ideal, as your password is still available in plain text in that file, but it's better than the first option.

</div>

#### Using the '::ask::' var adapter {: .block-title}
<div class="section-block" markdown="1">

The best way that is still straight-forward, at the moment, is to let the ``freckles`` application prompt you for the password. *freckles* has a feature called 'vars adapters' (which, in the future will be used to connect to password manages and the like, among other things). They can be activated by specifying the name of the adapter (between two sets of '::') as the argument value. The var adapter we use here is called 'ask'. So, in our example from before, we'd do:

```console
frecklecute user-exists --password ::ask:: markus

Input needed for value 'password': the user password in plain text
  password:
```

This way the password never hits the hard disk, nor is it exposed in plain text. The one advantage this has is that you now have an interactive script, which is not ideal if you want to use *freckles* within an automated pipeline or similar.

</div>

#### Using an Ansible lookup plugin {: .block-title}
<div class="section-block" markdown="1">

Leaky abstraction alarm, this is an advanced usage pattern! If you use the *freckles* Ansible adapter, and you know what you are doing, you can use [Ansible lookup plugins](https://docs.ansible.com/ansible/latest/plugins/lookup.html) directly.

Instead of providing the password value, you provide a value in the form of:

```console
frecklecute user-exists --password "{{ lookup('<lookup_plugin_name>', '<lookup_plugin_arg>' }}" markus
```

Check out the [list of lookup plugins](https://docs.ansible.com/ansible/latest/plugins/lookup.html#plugin-list) Ansible supports, and see if you find an appropriate one.

For example, to use that for reading a password from a file, we could do:

```console
frecklecute user-exists --password "{{ lookup('file', '/tmp/password' }}" markus
```

(btw, don't do that! Don't use a file in '/tmp' to store passwords! I'm only showing you the principle!)


Or, to read from an environment variable:

```console
frecklecute user-exists --password "{{ lookup('env', 'MY_PASSWORD' }}" markus
```

Those two examples don't improve on our password security situation at all though. So maybe we should use the local OS keyring? We'd do it like this:

```console
frecklecute user-exists --password "{{ lookup('keyring', 'my_user_passwords markus') }}" markus
```

Some of those lookup plugins need extra Python packages in the virtualenv that runs Ansible. This will be a 'context' specific setting soon, but is not implemented yet. You'll have to figure out how to do that manually for now.

</div>
</div>

### Internal password handling {: .section-title}
<div class="section-block" markdown="1">

This is a topic you can do nothing about, but I think you should know how *freckles* internally handles passwords. Most importantly, to be able to make an informed decision on whether you want to trust *freckles* with your passwords at all.

This behaviour is highly [adapter](/doc/adapters) dependent. As  the [nsbl adapter](/doc/adapters/nsbl) is the only functional one at the moment, I'll just describe that on here:

- you enter the password in one of the ways described above
- *freckles* keeps it in memory, and eventually hands it off to the adapter that runs the *frecklet* in question
- the 'nsbl' adapter takes the var_name/password map and replaces the password with a string like: ``{{ __secret_<variable_name>__ }}``
- it creates an Ansible vault file, using a randomly generated key and puts it into the playbook directory (using [this bash script](https://gitlab.com/nsbl/nsbl/blob/develop/src/nsbl/external/scripts/create-vault.sh) -- secret vars are provided by piping them via stdin)
- the ansible-playbook run is kicked off using '--vault-id=freckles_run@<vault_key_file>' (where vault_key_file is a named pipe) and the vault file we created earlier (here's the script that calls ansible-playbook: [wrapper script](https://gitlab.com/nsbl/nsbl/blob/develop/src/nsbl/external/nsbl-environment-template/%7B%7Bcookiecutter.env_dir%7D%7D/run_all_plays.sh))
- after the run is finished (or failed), both named pipes (the vault_key_file as well as the vault itself) are deleted

This is still not 100% ideal, as there is a chance that somebody with access to your account can do a sort of man-in-the-middle
attack in the milli-seconds when the named pipes are created. But if that actually happens you would be way beyond the point where you would worry about *freckles* security...

Last, but not least, *freckles* is written in Python, which does not allow to overwrite strings in memory to 'destroy' passwords once they are no longer needed (as far as I know -- do let me know if I'm wrong!!!). So this is a limitation we'll all have to live with, unfortunately.

</div>


### More? {: .section-title}
<div class="section-block" markdown="1">

Is there anything I forgot? Anything you would like to know, or point out? If you have any concern, or any idea how to make any of this more secure, please let me know!

I take this topic seriously, and I try to be as open and informed as my feeble mind and my time allow me to be. But I'm fully aware that there is quite a bit I don't know, so please give me as much feedback as you have. Every little bit helps!

</div>
