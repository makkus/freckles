---
title: Glossary
url_path_prio: 2000
---

adapter
:    *freckles* can execute tasks using different backends (shell, Ansible, etc.). An adapter implements an interface
     to that backend *freckles* can query and use. 

frecklecute:
:    One of the command-line application that ship with *freckles*. Takes a *frecklecutable* and executes it. Can auto-generate command-line arguments and help-text.

freckles:
:    All of this. *freckles* is the name of the overall framework, package, etc.

frecklet
:    The basic building block in *freckles*, a list of one or several tasks which in turn can refer to other *frecklets*.

frecklecutable
:    Technically also a *frecklet*, but used to refer to high-level *frecklets* that most likely will only be called directly
     by a user or script, not other frecklets. Basically a *frecklet* that has reached drinking-age.
