Installation guide
==================

You will need to install Python 2.7 and some Python modules, Ansible
from 2ndQuadrant's repository, and the AWS cli tools.

Python and modules
------------------

Install Python 2.7.x, pip, and virtualenv:

```
    # Debian or Ubuntu
    apt-get install python2.7 python-pip python-virtualenv

    # RedHat or CentOS
    yum install python python-pip python-virtualenv
```

Create and activate a virtualenv, to avoid installing Ansible's Python
module dependencies system-wide (highly recommended):

```
    virtualenv ~/ansible-python

    # The following line can go into your .bashrc/.profile
    source ~/ansible-python/bin/activate
```

Install the python dependencies:

```
    pip install -r python-requirements.txt
```

Install openvpn:
----------------

If you are planning to use the openvpn role, then you will need to install openvpn. Depending on your platform, corresponding commands might be needed.

Ubuntu:
```
    sudo apt-get install openvpn
```

Mac:
```
    sudo [brew or port] install openvpn
```

RedHat / CentOS:
```
    yum install epel-release
    yum install openvpn
```

Ansible
-------

You will need Ansible from the
[2ndQuadrant/ansible repository](https://github.com/2ndQuadrant/ansible).

Clone the Ansible repository:

```
    git clone --recursive https://github.com/2ndQuadrant/ansible
```

Set ANSIBLE_HOME in your environment (and .bashrc/.profile):

```
    export ANSIBLE_HOME=/path/to/ansibledir
```

Now you should be able to run ./utils/ansible and the other scripts in
this repository. The following simple tests should succeed if Ansible
has been installed correctly:

```
    ./utils/ansible localhost -m ping
    ./utils/ansible localhost -c ssh -a "id"
```

[The Ansible installation docs](http://docs.ansible.com/ansible/intro_installation.html)
have more details about running from a source checkout, but the steps
above should be all you need to get started.

Optional
--------

Install pwgen for better password generation (strongly recommended for
production clusters).

SELinux known issue
-------------------

A bug with virtualenv on some versions of a RHEL derivative host (RHEL and CentOS) can mean
this error is generated from ansible:
"Aborting, target uses selinux but python bindings (libselinux-python) aren't installed!"

A workaround is to copy selinux package into the virtual environment: 

```
    cp -rp /usr/lib64/python2.7/site-packages/selinux ~/ansible-python/lib/python2.7/site-packages
```

Help
----
Write to Abhijit, Gülçin, Haroon, or Nikhils for help with Ansible.
