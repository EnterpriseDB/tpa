---
title: TPAexec - Detailed Installation guide
version: 1.0
date: 01/June/2018
author: Craig Alsop
copyright-holder: 2ndQuadrant Limited
copyright-years: 2018
toc: true
---

TPAexec - Detailed Installation guide
===========================

© Copyright 2ndQuadrant, 2018. Confidential property of 2ndQuadrant; not for public release.



In addition to TPAexec, you will need to install Python 2.7 and some Python modules, Ansible
from 2ndQuadrant's repository, and the AWS cli tools.
It is suggested that the TPAexec should be configured and run from a non-root account

Commands run as root will be shown starting with a **[root]#** and commands run as tpa user will be shown starting with a **[tpa]$**

### RedHat/CentOS specifics

Additional required packages not in base RedHat/CentOS build:

```
    [root]# yum install git gcc ntp
```

## TPAexec

Clone the TPAexec repository

```
    [tpa]$ git clone --recursive https://github.com/2ndQuadrant/TPA
```
Set TPA_HOME and add the TPA bin directory to your path in the TPAexec user environment (and .bashrc / .profile):
```
    [tpa]$ export TPA_HOME=/path/to/TPA
    [tpa]$ export PATH=$PATH:$TPA_HOME/bin
```


Python and modules
------------------

Install Python 2.7.x, pip, and virtualenv:

```
    # Debian or Ubuntu
    [root]# apt-get install python2.7 python-pip python-virtualenv

    # RedHat or CentOS
    [root]# yum install python python-pip python-virtualenv
```

Create and activate a virtualenv, to avoid installing Ansible's Python
module dependencies system-wide (highly recommended):

```
    [tpa]$ virtualenv ~/ansible-python

    # Activate ansible-python ( and add command to .bashrc/.profile)
    [tpa]$ source ~/ansible-python/bin/activate
```

Install the python dependencies:

```
    [tpa]$ pip install -r python-requirements.txt
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
    [brew or port] install openvpn
```

RedHat / CentOS:
```
    [root]# yum install epel-release openvpn
```

Ansible
-------

You will need Ansible from the
[2ndQuadrant/ansible repository](https://github.com/2ndQuadrant/ansible).

Clone the Ansible repository:

```
    [tpa]$ git clone --recursive https://github.com/2ndQuadrant/ansible
```

Set ANSIBLE_HOME in your environment (and .bashrc / .profile):

```
    [tpa]$ export ANSIBLE_HOME=/path/to/ansibledir
```

Make sure your date & time are correct, as various things will fail if these are wrong

```
    [root]# ntpdate time.apple.com
```

Now you should be able to run ./ansible/ansible from your local copy of the TPA repository. 
The following simple tests should succeed if Ansible has been installed correctly:

```
    [tpa]$ $TPA_HOME/ansible/ansible localhost -m ping
    [tpa]$ $TPA_HOME/ansible/ansible localhost -c ssh -a "id"
```

[The Ansible installation docs](http://docs.ansible.com/ansible/intro_installation.html)
have more details about running from a source checkout, but the steps
above should be all you need to get started.

Recommended
-----------

Install pwgen for better password generation (strongly recommended for production clusters).

SELinux known issue
-------------------

A bug with virtualenv on some versions of a RHEL derivative host (RHEL and CentOS) can mean this error is generated from ansible:
"Aborting, target uses selinux but python bindings (libselinux-python) aren't installed!"

A workaround is to copy selinux package into the virtual environment: 

```
    [tpa]$ cp -rp /usr/lib64/python2.7/site-packages/selinux \
    ~/ansible-python/lib/python2.7/site-packages
```

Help
----
Write to tpa@2ndQuadrant.com for help with Ansible.

------

[^Information Classification: Internal]: [ISP008] Information Classification Policy

