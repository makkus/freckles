.. _freckles_profile_overview:
=============================
**freckles** profile overview
=============================

*freckles* needs a set of descriptions that describe what to do if it finds data or code (a *freckle*) of a certain type.

At the moment only 2 such descriptions (lets call them *profiles* for lack of a better term) are implemented: ``dotfiles`` and ``python-dev``. *freckles* is written in a way so more of those can be added fairly easily, as I think it'd be quite useful to have a set of collaboratively developed and agreed upon descriptions on how a certain type of data or code should be structured, which metadata is necessary to describe certain 'expressions' of such data or code, and how to 'setup' said data or code.

Ideally, the metadata that describes the characteristics of a *freckle* will sit with the *freckle* itself, in its repository. Apart from a few minor exceptions, like for example into which location to check-out a repository, that metadata should not be dependent on the peculiarities of the target system.

Following is a list of currently available *profiles*, and links to more in-detail descriptions of those:

:doc:`freckles_profile_dotfiles`

     Used with a repository of dotfiles (configuration files), and metadata describing which applications to install alongside. Basically a way to configure your working environment and make it easy to (re-)install it when and where-ever you need.

:doc:`freckles_profile_python_dev`

     Used for Python projects that are layed out similar to what you get when you use (XXX link to cookiecutter)
