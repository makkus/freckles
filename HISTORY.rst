=======
History
=======

0.4.6
-----

* blueprint feature, freckelize can now use templates and doesn't need pre-existing data
* improvements to `freckelize`, can take extra variables via commandline now
* added 'inaugurate' and 'frankentree' scripts to freckles package
* added 'frkl' abbreviation, points to the 'freckles-io' github account

0.4.5 (2017-12-07)
------------------

* refactored `freckelize`: checkout phase is now a separate run, which enables:
* auto-detecting freckle repo profile(s)
* minor bug fixes and improvements


0.4.4 (2017-11-04)
------------------

* changed `frecklecutable` Jinja2 markers to be '{{::', '::]]', '{%::' and '::%}'

0.4.3 (20017-10-30)
-------------------

* Added 'ansible-tasks' adapter
* Improved 'change-freckles-version' *frecklecutable*, allows to use current git master, as well as a local source folder
* Fixed several issues with adding extra repos
* Updated ansible to 2.4.1.0, also updated other dependencies
* Updated mac-os-x-cli-tools & homebrew roles

0.4.2 (2017-10-22)
------------------

* Added options 'change-freckles-version' to frecklecutable: allow local folder, or 'git' for git master branch
* Make sure 'python-apt' is installed if on platform with 'apt' package manager

0.4.1 (2017-10-19)
------------------

* Renamed default frecklecutables using more specific names (so they can be better used as 'standalone' scripts if in PATH)

0.4.0 (2017-10-18)
------------------

* First public release on PyPI.
