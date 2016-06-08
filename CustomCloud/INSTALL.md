CustomCloud installation
========================

To use CustomCloud, you will need Ansible from the
[Upstream Ansible repository](https://github.com/ansible/ansible).

For some reason if you get issues with upstream Ansible then you can
also try the [2ndQuadrant/ansible repository](https://github.com/2ndQuadrant/ansible).

(2ndQuadrant/ansible is a curated version of the official ansible
repository's devel branch, with some additional useful changes that have
not yet been merged upstream.) Latest tests with upstream Ansible are
working fine, so probably 2ndQuadrant sources might not be needed.

The quick version: clone Ansible sources, export
ANSIBLE_HOME=/path/to/clone, and invoke ansible through the
utils/ansible wrappers provided here.

Python and modules
------------------

Install Python 2.7.x and any packages needed to get pip and virtualenv
working. For example, on Ubuntu, install 

* python2.7 
* python-pip
* python-virtualenv

To avoid installing the modules system-wide, they can go into an
ansible-specific virtualenv (highly recommended). Once done, create
a virtual env

```
    virtualenv ~/ansible-python

    # The following line can go into your .bashrc
    source ~/ansible-python/bin/activate
```

You will need recent versions of the following Python modules:

* PyYAML
* jinja2
* boto
* PyCrypto
* six

Install these modules using pip ("pip install jinja2 boto …") rather
than your operating system's packages (which are often too old).


```
    # With the virtualenv activated, install packages
    pip install jinja2 PyYAML boto PyCrypto six
```

Ansible
-------

Clone the Ansible repository:

```
    git clone --recursive https://github.com/ansible/ansible

    or 

    git clone --recursive https://github.com/2ndQuadrant/ansible
```

Set ANSIBLE_HOME in your environment (and .bashrc):

    export ANSIBLE_HOME=/path/to/ansibledir

Now you should be able to run ./utils/ansible and the other scripts in
this repository. The following simple tests should succeed if Ansible
has been installed correctly:

    ./utils/ansible localhost -m ping
    ./utils/ansible localhost -c ssh -a "id"

[The Ansible installation docs](http://docs.ansible.com/ansible/intro_installation.html)
have more details about running from a source checkout. But the above steps should
be enough really to get you going with Ansible.

If you have trouble getting Ansible working, write to Abhijit, Richard,
Haroon, Nikhils or Ian for help.

Other software
--------------

The [AWS CLI](https://aws.amazon.com/cli/) can be useful, but you
probably won't need it. This is not needed for TPA. 

If for some reason you do need it, follow the instructions at
http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/ec2-cli-get-set-up.html
