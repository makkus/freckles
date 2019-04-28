---
title: Glossary
url_path_prio: 2000
---

I'm aware the 'freck***'-based wording I've got going around here is probably a bit silly. But, for one, it serves the purpose of slightly annoying people who get slightly annoyed by those things (consider it my contribution to those peoples' character-building: Just relax and worry about the important things, (wo)man!). And once I had the name 'freckles', it was just the natural and easy thing to do, sorta.

Also, much more importantly, there is this certain type of person I've encountered in my working life, who consider themselves to be 'professional' (with a very boring definition of 'professional') and always act all serious, but in my opinion they are just a bit full of themselves. I want those people to have to use words like '*frecklecutable*'.

The one slight disadvantage is that people might also become a bit confused. Hence, glossary:

adapter
:    *freckles* can execute tasks using different backends (shell, Ansible, etc.). An adapter implements an interface
     to that backend *freckles* can query and use.

frecklecute
:    One of the command-line application that ship with *freckles*. Takes a *frecklecutable* and executes it. Can auto-generate command-line arguments and help-text.

freckles
:    All of this. *freckles* is the name of the overall framework, package, etc.

frecklet
:    The basic building block in *freckles*, a list of one or several tasks which in turn can refer to other *frecklets*.

frecklecutable
:    Technically also a *frecklet*, but used to refer to high-level *frecklets* that most likely will only be called directly
     by a user or script, not other frecklets. Basically a *frecklet* that has reached drinking-age.
