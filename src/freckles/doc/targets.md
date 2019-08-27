---
title: Targets
url_path_prio: 160
draft: false
---

*freckles* can be used both to setup the local machine (say, your laptop), as well as remote ones, using the exact same command, except for an additional ``target`` argument.

There are a few slight differences when using *freckles* on a local target as opposed to a remote one though, and there are a few different 'remote' connection types that are supported. Please find details about those below.

So, for the sake of illustration, we'll run the same *frecklet* in a few different ways, on different targets. For this we'll use the fairly simple, but non-trivial [static-website-from-string](https://freckles.io/frecklets/default/web/static-website-from-string) *frecklet*, which will [install an Nginx webserver](https://freckles.io/frecklets/default/service/webserver-service) (if not already present), setup a [Nginx server block to host a static website](https://freckles.io/frecklets/default/web/static-website-from-folder), and then [create a file](https://freckles.io/frecklets/default/filesystem/file-with-content) that contains html to be servced by our webserver.

### *local* target {: .section-title}
<div class="section-block" markdown="1">

*Local* targets are the default, so, for the command-line interfaces (``freckles``, ``frecklecute``), if you don't specify the target argument (``--target``/``-t``) *freckles* assumes you want it to execute its instructions locally. So, assuming we have a terminal open on the machine we want to install (either our local machine, a VM or LXD container, or a remote machine we ssh-ed into), we can issue:

```console
frecklecute static-website-from-string --content '<h1>Hello World!</h1>'
```

</div>

### *remote* targets {: .section-title}
<div class="section-block" markdown="1">



</div>
