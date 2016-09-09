CustomCloud installation
========================

To use CustomCloud, you will need Ansible from the
[2ndQuadrant/ansible repository](https://github.com/2ndQuadrant/ansible).

(2ndQuadrant/ansible is a curated version of the official ansible
repository's devel branch, with some additional useful changes that have
not yet been merged upstream.)

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

CustomCloud needs recent versions of specific Python modules. After activating your virtualenv, they can be installed as below:

```
    pip install -r /path/to/TPA/CustomCloud/python-requirements.txt
```

Ansible
-------

Clone the Ansible repository:

```
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


Other software
--------------

Follow the instructions at
http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/ec2-cli-get-set-up.html
to install the [AWS CLI](https://aws.amazon.com/cli/).

On Ubuntu, even a basic: 

```
    sudo apt install awscli
```
works ok enough for example.

--------------
Write to Abhijit, Gülçin, Haroon, or Nikhils for help with Ansible.


