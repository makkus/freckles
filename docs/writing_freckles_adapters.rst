As *freckles* uses *ansible* as the backend technology to do all the heavy lifting, `all ansible modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_, and `all roles on ansible galaxy <https://galaxy.ansible.com>`_ are readily available to be re-used in *freckles adapters*.

A *freckle adapter* consists of 2 to 3 text files, located in the same folder. The first one, ``freckles-adapter.yml`` is a metadata file that contains a description of its purpose, (optinal) command-line argument definitions to enable users to provide input to change the default behaviour, and default variables, if necessary.

The other 2 files are similar to ansible playbook files in format, and only one of them is required, which one is up to the developer and use-case. It is possible to use all 2 though, of course:

``init-tasks.yml``
    this contains tasks that only have to be executed once, even if *freckles* processes multiple *freckle* folders of the same data type. An example would be a 'static webpage' datatype, where the webserver to host the page(s) only needs to be installed once, independent of how many websites are hosted.

``freckle-tasks.yml``
    this contains tasks that have to be executed once for every *freckle* folder that is processed. Using the example of a webserver, this file would contain for example tasks to create a virtual host for every 'website freckle'.

For examples, check out the source code of the default adapters *freckles* comes with:
