============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.


Licensing
---------

Please be aware that this project is licensed under the `Parity Public
License <https://licensezero .com/licenses/parity>`_. This basically
means it is allowed to use this code for free, except in combination
with code that is not open-source. For more details, please read the
license text itself (it's short!) and check out
https://freckles.io/licensing (which still has to be written).

In order to preserve the option to be able to re-license my code later
on, as well as sell private licenses for use with non-open-source use,
external contributions to this project need to be licensed using a
more permissive license (`Simplified BSD
<https://opensource.org/licenses/BSD-2-Clause>`_). This doesn't mean
you give up the copyright to your contributed code, but it gives me
(and others) the right to use and integrate your code without many
restrictions.

If those terms are acceptable to you, please read on! If not, I won't
be able to accept your contribution at this time.


GitLab
------

This project is hosted on GitLab, which means you'll have to have an
account there in order to contribute. Obviously.


Signed commits
--------------

In order to a) be able to verify the contributed code is actually from
you, and b) be able to document that I'm allowed to use code
contributed by a 3-rd party I will only accept signed commits.

If you don't already have a gpg key setup, I'd recommend using
following `this guide on GitLab.com
<https://docs.gitlab.com/ee/user/project/repository/gpg_signed_commits/>`_,
or use `keybase <https://keybase.io>`_ to setup a gpg key, add that key
to your GitLab account and follow `a tutorial like this
<https://github.com/pstadler/keybase-gpg-github>`_ (just replace
GitHub with GitLab).


Get Started!
------------

1) Add and sign the 'Developer Certificate of Origin'
+++++++++++++++++++++++++++++++++++++++++++++++++++++

Before you submit your first contribution, fork this repository,
create a folder with your GitLab username under the ``contributing/contributors``
folder, copy the ``doc_and_license.txt`` file that can be found in
this folder into it, and create a pull request::

    $ git clone https://gitlab.com/<your_gitlab_username>/freckles.git
    $ cd freckles/contributing
    $ mkdir <your_gitlab_username>
    $ cp doc_and_license.txt <your_gitlab_username>
    $ git add <your_gitlab_username>
    $ git commit -m "Signed DCO <your_gitlab_username>"
    $ git push origin develop


If you want, add a '<gitlab_username>.rst' document in the ``contributing/contributors/<gitlab_username>/``
folder and introduce yourself, add contact information or anything else you think makes sense.

2) Start contributing code
++++++++++++++++++++++++++

1. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv freckles
    $ cd freckles/
    $ python setup.py develop

2. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

3. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8
    $ pytest
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv or do a
   ``pip install -r requirements_dev.txt`` in the project root to get
   all the development dependencies I use.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitLab website.


Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 2.7, 3.4, 3.5 and 3.6, and
   for PyPy. Check https://gitlab.com/freckles-io/freckles/pipelines
   and make sure that the tests pass for all supported Python versions.
