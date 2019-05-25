---
title: Security
url_path_prio: 200
draft: false
---

## Security considerations {: .section-title}
<div class="section-block" markdown="1">

Security is an important topic, even more so when sudo/root permissions are involved. I am not comfortable I'll be able to do the topic
justice on here, as there are just too many variables and scenarios. So please make sure you are always aware what you are doing, and consult
other sources for anything that is not covered here. Probably good idea to do that even for things that are covered here!.

### *freckles* installation {: .block-title}
<div class="section-block" markdown="1">

Quite deliberately, *freckles* will never require any sudo/root permissions when installed or run by itself. It will only ask you for a sudo password
when you tell it to run tasks that require them.

The *freckles* application is a single binary, and thus can be downloaded and placed anywhere on the filesystem. It is usually a good idea
to put it in a folder that is in your sessions [``PATH``](https://www.cs.purdue.edu/homes/bb/cs348/www-S08/unix_path.html).

You can either download it manually, or use the [freck](https://gitlab.com/freckles-io/freck), the *freckles bootstrap script*, to do it for you.
</div>

#### The bootstrap script
<div class="section-block" markdown="1">

'Curly bootstrap scripts' like the *freckles* one are sometimes frowned up as being inherently less secure than any alternatives. I don't think
that is actually true in a lot of cases, but if you don't want to take any chances, just do everything manually and don't think about it.

In my mind, if you trust somebody enough to run their application, you might as well trust their bootstrap script, and that they wrote it, and set it up
using the same common sense they use when writing their application. There are edge cases, and its up to you to decide whether you are ok with them.

In the case of *freckles*, the one advantage manually downloading the binary to using the bootstrap script I can see is that the bootstrap script
could have been modified by a 3rd party. But, if that 3rd party has access to the bootstrap script, they would have also have had access to the binary, so there is really not much gained here.

The script itself offers some neat features, first and foremost it lets you execute *freckles* straight away, in the same command you download it, and also, if you want, it can delete *freckles* and any intermediate files there were created during a run after it finished. This is really convenient for one-of install runs on vanilla servers that don't need to be touched again after, or when building Docker images.

If you use that a lot, I'd recommend you host the script yourself though, and maybe also the *freckles* binary. It is not finished yet, but I'm working on a *frecklet* that can setup a web-server to host *freckles* and a customizable bootstrap script, that is tailored to your environment and requirements. Stay tuned, and ping me if that interests you.

</div>

#### Binary signing
<div class="section-block" markdown="1">

Currently, only the Mac binary of *freckles* is signed. The plan is to also sign Linux binary, or at least provide hashes, but public opinion seems to be
split of whether that provides really any advantage over just serving the binaries over https. I'm not really sure, happy to get some input if you have some.

</div>

### running *freckles* {: .block-title}
<div class="section-block" markdown="1">

As was mentioned above, *freckles* only asks you for sudo/root passwords when the task you want it to execute requires it. Sometimes *freckles* will be
run with root permissions, for example when run inside a Docker build process. Sometimes a system is setup so that there exists an admin user who has
access to sudo without having to provide a password. In fact, *freckles* comes with [a *frecklet*](/frecklets/system/passwordless-sudo-users) to setup just that.

#### 'Trusted' *frecklets*

To somewhat mitigate users executing harmful *frecklets*, *freckles* comes with two sets of *frecklets* by default, which come with their own sort of 'trust levels'. The *frecklets* from the [default](/frecklets/default) repository are vetted by the *freckles* developer himself (aka, me), so if you trust *freckles*, can probably also trust those. The [community](/frecklets/community) *frecklet* repository is created (or will be, hopefully) and curated by the community. There will be a few eyes on the contents of the *frecklets*, which I hope makes it unlikely somebody will be able to sneak in something malicious. Again, this is something you have to judge for your self, I can only try to explain the situation, so you can just the risk/value ratio yourself.

#### Remote repo permission config

Related to that, by default *freckles* does not allow any outside *frecklets* to be run, it does not even allow you to change the configuration to allow them, unless you [unlock the configuration](/configuration/contexts). After that, you can add repositories to the 'allow_remote_whitelist', or set the 'allow_remote' configuration value to 'true'. Again, this is your own decision, and you should make an informed one.

#### Entering passwords

Some *frecklets* need passwords as user input. This is a difficult thing to do securely. *freckles* still misses a few features that will make handling
passwords better, easier, and more secure. In the future there will be integration to password stores (e.g. Hashicorps Vault, Bitlocker, the OS keychain, ...). For now, there are only a few (more basic) options, so it's a good idea you know about them, and can pick the best one for your scenario.

When writing a *frecklet*, you can mark arguments ``secret``, which will tell *freckles* to handle them differently to 'normal' ones. All the *frecklets*
in the 'default' and 'community' repositories use that, but if you use a *frecklet* from somebody else, have a look at it's content and make sure it
is done properly. That is probably also a good indicator on that *frecklets* quality...

It is not a good idea to just use passwords as normal cli arguments, ala:

```console
frecklecute user-exists --password password123 markus
```

Even though *freckles* will internally handle this value in a secure manner, this command will show up in your shell history file (including the password string), so you should prefer to never do that. One option you have is to use the ``freckles`` or ``frecklecute`` ``-v vars_file`` argument, point it to a file that is only readable by you (``chmod 0700 vars_file``), and include your password there. This is by no means ideal, as your password is still available in plain text in that file, but it's better than the first option.

The best way, at the moment, is to let the ``freckles`` application prompt you for the password. *freckles* has a feature called 'vars adapters' (which, in the future will be used to connect to password manages and the like, among other things). They can be activated by specifying the name (between two sets of '::'s) of the adapter as the argument value. The var adapter we use here is called 'ask'. So, in our example from before, we'd do:

  ```console
frecklecute user-exists --password ::ask:: markus

Input needed for value 'password': the user password in plain text
  password:
```

This way the password never hits the hard disk, nor is it exposed in plain text. The one advantage this has is that you now have an interactive script, which is not ideal if you want to use *freckles* within an automated pipeline or similar.

As I said, there are plains to improve on all this, but nothing is implemented yet.

#### Internal password handling

This is a topic you can do nothing about, but I think you should know how *freckles* internally handles passwords. Most importantly, to be able to make an informed decision on whether you want to trust *freckles* with your passwords at all.

This behaviour is highly [adapter](/doc/adapters) dependent. As  the [nsbl adapter](/doc/adapters/nsbl) is the only functional one at the moment, I'll just describe that on here:

- you enter the password in one of the ways described above
- *freckles* keeps it in memory, and eventually hands it off to the adapter that runs the *frecklet* in question
- the 'nsbl' adapter takes the var_name/password map and replaces the password with a string like: ``{{ lookup('env', <var_name>) }}``
- the adapter kicks off the Ansible run, putting the password in the environment with the 'var_name' as key
- whenever a task needs access to a password value, Ansible will use the ['env'](https://docs.ansible.com/ansible/latest/plugins/lookup/env.html) lookup plugin to retrieve it from the environment
- once the Ansible run is finished, the runtime environment will be deleted by the OS

This is not 100% ideal, but the best I could come up with for now. It means that users on the same machine that have elevated privileges have temporarily access to the password (while the Ansible process is running), via ``/proc/<pid>/environ``. Let me know if you have a better idea on how to do that, I'm very keen to hear suggestions.

I do think it's an acceptable situation, but I would say that, wouldn't I? :-)


Last, but not least, *freckles* is written in Python, which does not allow to overwrite strings in memory to 'destroy' passwords once they are no longer needed (as far as I know -- do let me know if I'm wrong!!!). So this is a limitation we'll all have to live with, unfortunately.

</div>

</div>


### More?
<div class="section-block" markdown="1">

Is there anything I forgot? Anything you would like to know, or point out? Please do get in touch if that is the case,
I take this topic seriously, and I try to be as open and informed as my feeble mind and my time allow me to be. But I'm
 fully aware that there is quite a bit I don't know, so please give me as much feedback as you have. Every little bit helps!
