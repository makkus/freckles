=====
Trust
=====

freckles bootstrap
------------------

So, you think it's sorta bad that all those newfangled projects nowadays want you to download a script with curl or wget and pipe it directly into bash? I agree. It is sorta bad. First and foremost from a security perspective of course, but also for a number of other reasons. *freckles* is not in any way better, and in some regards even worse. For now, I'm not quite sure what else to do though, especially given one of my main objectives, which is to be able to setup a workstation with a one-liner, without having to install *freckles* and it's dependencies manually before executing the first run. Of course I give that option, but I'm not sure how much better that really is, since, if you intend to use *freckles* you have to trust it's code in the first place. So running a bootstrap script from my github page/domain redirect is not really that much worse than trusting my *freckles* package on pip (which is what you'll have to do in either case).

installer scripts used by freckles
----------------------------------

Then there is the matter of freckles installing package managers like *nix*, *conda*, or *homebrew*. Some of those are also installed using the recommended method, which is downloading a script with curl or wget and piping it directly into bash. I'm not really too happy doing this, but I don't really

Applying freckles configurations
--------------------------------

I'm not sure whether people will end up using *freckles* at all, and how much they like or dislike its configuration format. As I've mentioned somewhere else, that 'elastic' configuration format is an experiment, and it might turn out to be way too involved and unusable for other people to even consider picking it up. If there is any sort of usage from other people than myself though, it might turn out that people share configurations on how to setup certain projects (like the one that sets up a *freckles* dev environment) or working environments
