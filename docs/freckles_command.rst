============
``freckles``
============

Description
-----------

*freckles* uses adapters to deal with data or code of a certain profile/type (a *freckle*).

At the moment only 2 such adapters are implemented: ``dotfiles`` and ``python-dev``. *freckles* is written in a way so more of those can be added fairly easily, as I think it'd be quite useful to have a set of collaboratively developed and agreed upon descriptions on how a certain type of data or code should be structured, which metadata is necessary to describe certain 'expressions' of such data or code, and how to 'setup' said data or code. This is already being done in a lot of cases, there is just no generic way to handle all the different types of data yet.

Ideally, the metadata that describes the characteristics of a *freckle* will sit with the *freckle* itself, in its repository. Apart from a few minor exceptions, like for example into which location to check-out a repository, that metadata should not be dependent on the peculiarities of the target system.

Usage
-----

.. click:: freckles.freckles_cli:cli
  :prog: freckles
  :link-command-prefix: adapters
