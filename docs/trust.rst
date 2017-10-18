#####
Trust
#####

This is a fairly important topic, especially for a tool like *freckles* which downloads and uses bits and pieces from all over the place. On this page I'll tell you what I think makes sense (or at least is practical) in terms of security, be aware that I'm not always sure about what to do in that area myself, and that it's very likely that some of the things I'm writing about will probably be wrong.

Use your own judgment, and brain.

Bootstrap scripts
*****************

First of all, as you've probably seen, you don't have to use the *'inaugurate'* bootstrap script to get *freckles* running. So, if you feel better that way, just `install it manually <Install manually via pip>`_.

That being said, it probably doesn't make much sense in terms of being 'more secure'. I've always wondered why shell scripts that are downloaded and executed directly get a so much worse rep than all the other programms we install on our computers.

Because, most of the time those bootstrap scripts are offered and written by the people who have also written the applications those scripts install. It doesn't make much sense to trust somebody to write a python package that is hosted on *pypi* (or whatever the other language specific repos are for nodejs, Java, Ruby, etc), but not the bootstrap script that installs said package from *pypi*. Except, of course, that person has a reputation for writing really terrible bash scripts, but is otherwise a decent Python programmer. But that's a different issue then.

Trust threshold
***************

Basically, in my opinion, you have to think about and decide who you trust (enough) to run applications written by them on your computer. Making that decision is hard, because you hardly know any of the people writing the tools you are using. Depending on the machine you are running those applications on, you might have to tighten security a bit, or you might be able to loosen it. If the application needs root access, you might up the trust-threshold a bit, but in the end it doesn't make much difference. If somebody tries to do something, even normal user access can be exploited quite badly. If it's just a virtual machine or container, you can probably install programs from more sketchy sources, as it's less likely to cause real harm in such a contained environment.


Community
*********

So, how to decide which applications to install, and which to better not use at all?

I honestly don't know, I think there is no real good answer. Ideally, all you would ever install are applications that come with your distribution. After choosing a distribution/OS that has a good reputation.

If you need to install more recent versions, or applications that are not in your distributions repositories, try to limit yourself to widely used packages, as you can reasonably assume that the bigger the community, the more eyes were on the source code.

If you need to install something niche, install it in a container, or Virtual Machine (ideally, use something like `Qubes <https://www.qubes-os.org/>`_!).

freckles
********

So, what about *freckles*? Obviously, I'm not the best person to give advice here.

Obviously I'd like you to be able to  use *freckles* if you think it's interesting, or useful. I do hope there'll be a reasonably sized community around it at some stage, but that might never happen. Maybe start using it in your Vagrant containers, not your main machine or production servers (you shouldn't do that anyway, since *freckles* is nowhere near production quality code yet).

*freckles* can download and execute *ansible roles*, *frecklecutables*, and *freckelize adapters* from online repos. This is one of the main features of *freckles*, and it is the reason why it can get a machine into the state you want it to be without anything other on the box than ``curl`` or ``wget``.

That means you have to be careful which of the bits and pieces you download and use.

inaugurate
==========

I'd recommend you read the `inaugurate script <https://github.com/makkus/inaugurate/blob/master/inaugurate.sh>`_ that is used to bootstrap *freckles* thorougly, then host it somewhere on your own infrastructure. That way you can be sure no changes were made since the last time you looked.
You can always updated it once you review the commit log on it's repository.

Ansible roles
=============

Not sure about those, as at the moment people seem to be using them mostly straight out of Ansible galaxy, without much care. Ansible Galaxy, like a lot of 'official' language/framework repos is not audited as far as I know (nor would I expect it to be), so it'd be fairly easy to sneak in something malicious. For anything of importance, I'd recommend creating your own "role collection" on Github (using ``git submodule`` or ``git subtree``) and put roles you have reviewed personally in there. Reviewing a role is fairly quick, as you really only need to go through the list of tasks to see what it does.

Sometime in the (hopefully near) future, my plan is to host two community repositories: `freckles-io roles <https://github.com/freckles-io/roles>`_ and the `ark <https://github.com/freckles-io/ark>`_. The former will be a collection of curated roles that are generally considered useful in the context of *freckles*, the latter I'd like to be a place where there is one high-quality role (and one role only) for any specific task (i.e. install nginx, setup Postgresql, etc.). I haven't gotten around to write up some requirements for roles to end up in the *ark*, but it'll be something like: "support the latest versions of all the major Distros, Mac OS X (if applicable), have testing and a maintainer, etc".

If that works out, and there really is no indication at all that it will, this could be a place to get 'somewhat trustworthy' Ansible roles from. If you think this is a good idea, and you'd like to help, ping me!

frecklecutables
===============

There are two parts to those: the script itself, and the roles it might or might not call. As *frecklecutables* are fairly easy to read, it should be easy and quick enough to scan and see whether they do what you expect them to do. If they call roles, you'll have to look those up, and check out the tasks in them as well. No way around it, I reckon.

As with roles, you can put *frecklecutables* you trust in their own repository (or even the same as the roles).

freckelize adapters
===================

Similar to *frecklecutables*, the adapters themselves are fairly easy and quick to read. But they also can call Ansible roles, which means, again, you'll have to look those up and read their task list if you want to make sure nothing untoward will happen if you use them.

Again, you can put *adapters* you trust in their own repository or alongside your *frecklecutables* and roles.
