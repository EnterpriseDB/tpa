---
title: TPAexec - Detailed Installation guide
version: 1.1
date: 11/June/2018
author: Craig Alsop
copyright-holder: 2ndQuadrant Limited
copyright-years: 2014-2018
toc: true
---

TPAexec - Detailed Installation guide
===========================

© Copyright 2ndQuadrant, 2018. Confidential property of 2ndQuadrant; not for public release.



In addition to TPAexec, you will need to install Python 2.7 and some Python modules, Ansible
from 2ndQuadrant's repository, and the AWS cli tools.
It is suggested that the TPAexec should be configured and run from a non-root account

Commands run as root will be shown starting with a **[root]#** and commands run as tpa user will be shown starting with a **[tpa]$**

Make sure your date & time are correct, as various things will fail if these are wrong
```
    [root]# ntpdate time.apple.com
```

## Packages
### Required

#### Python and modules
Install Python 2.7.x, pip, and virtualenv:

```
    # Debian or Ubuntu
    [root]# apt-get install python2.7 python-pip python-virtualenv

    # RedHat or CentOS
    [root]# yum install python python-pip python-virtualenv
```
#### RedHat/CentOS specifics

Additional required packages not in base RedHat/CentOS build:
```
    [root]# yum install git gcc ntp
```
### Recommended
Install pwgen for better password generation (strongly recommended for production clusters).
If you are planning to use the openvpn role, then you will need to install openvpn.
```
    # Debian or Ubuntu
    [root]# apt-get install pwgen
    [root]# apt-get install openvpn

    # RedHat or CentOS
    [root]# yum install pwgen
    [root]# yum install epel-release openvpn
    
    # Mac
    [brew or port] install pwgen
    [brew or port] install openvpn
```

## TPAexec

### Option 1 - from package (recommended if possible)

This will install TPAexec into /opt/2ndQuadrant/TPA/
```
    # Debian or Ubuntu
    [root]# apt-get install tpaexec-<version-number.os-type>_all.deb

    # RedHat or CentOS
    [root]# yum install tpaexec-<version-number>.noarch.rpm
```
Set TPA_HOME and add the TPA bin directory to your path in the TPAexec user environment (and .bashrc / .profile):
```
    [tpa]$ export TPA_HOME=/opt/2ndQuadrant/TPA/
    [tpa]$ export PATH=$PATH:$TPA_HOME/bin
```
Create and activate a virtualenv, to avoid installing Ansible's Python
module dependencies system-wide (highly recommended):

```
    [tpa]$ virtualenv ~/ansible-python

    # Activate ansible-python ( and add command to .bashrc/.profile)
    [tpa]$ source ~/ansible-python/bin/activate
```

Install the python dependencies into the virtualenv (including ansible:
```
    [tpa]$ $TPA_HOME/misc/tpa-pip-install.sh
```
Set ANSIBLE_HOME & ANSIBLE_LOG_PATH in your environment (and .bashrc / .profile):
```
    [tpa]$ export ANSIBLE_HOME=~/ansible-python
    [tpa]$ export ANSIBLE_LOG_PATH=~/ansible.log
```
Now you should be able to run ./ansible/ansible from your local copy of the TPA repository. 
The following simple tests should succeed if Ansible has been installed correctly:

```
    [tpa]$ $TPA_HOME/ansible/ansible localhost -m ping
    [tpa]$ $TPA_HOME/ansible/ansible localhost -c ssh -a "id"
```

------

### Option 2 - install from repositories

Clone the TPAexec repository

```
    [tpa]$ git clone --recursive https://github.com/2ndQuadrant/TPA
```
Set TPA_HOME and add the TPA bin directory to your path in the TPAexec user environment (and .bashrc / .profile):
```
    [tpa]$ export TPA_HOME=/path/to/TPA
    [tpa]$ export PATH=$PATH:$TPA_HOME/bin
```

You will need Ansible from the [2ndQuadrant/ansible repository](https://github.com/2ndQuadrant/ansible).

Clone the Ansible repository:

```
    [tpa]$ git clone --recursive https://github.com/2ndQuadrant/ansible
```

Set ANSIBLE_HOME in your environment (and .bashrc / .profile):

```
    [tpa]$ export ANSIBLE_HOME=/path/to/ansibledir
```


Now you should be able to run ./ansible/ansible from your local copy of the TPA repository. 
The following simple tests should succeed if Ansible has been installed correctly:

```
    [tpa]$ $TPA_HOME/ansible/ansible localhost -m ping
    [tpa]$ $TPA_HOME/ansible/ansible localhost -c ssh -a "id"
```

[The Ansible installation docs](http://docs.ansible.com/ansible/intro_installation.html)
have more details about running from a source checkout, but the steps above should be all you need to get started.

------



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
