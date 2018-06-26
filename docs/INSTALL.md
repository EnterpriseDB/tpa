---
title: TPAexec - Detailed Installation guide
version: 1.2
date: 14/June/2018
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
As root, create and populate a virtualenv, to avoid installing Ansible's Python module dependencies system-wide (highly recommended):

```
    [root]# virtualenv /opt/2ndQuadrant/TPA/tpa-virtualenv
    # Activate it so that we can install pip modules
    [root]# source /opt/2ndQuadrant/TPA/tpa-virtualenv/bin/activate
    # Install the python dependencies into the virtualenv (including ansible)
    [root]# /opt/2ndQuadrant/TPA/misc/tpa-pip-install.sh
```
For RedHat or Centos, workaround an SELinux bug
```
    # RedHat or CentOS
    [root]# cp -rp /usr/lib64/python2.7/site-packages/selinux \
    /opt/2ndQuadrant/TPA/tpa-virtualenv/lib/python2.7/site-packages
```
Set TPA_DIR and add the TPA bin directory to your path in the TPAexec user environment (and .bashrc / .profile):
```
    [tpa]$ export TPA_DIR=/opt/2ndQuadrant/TPA/
    [tpa]$ export PATH=$PATH:$TPA_DIR/bin
```
It is suggested that a `~/tpa` is created, which can contain TPA related files and directories.
```
    [tpa]$ mkdir ~/tpa
    # Copy the example clusters directory
    [tpa]$ cp -r $TPA_DIR/clusters tpa
```

Activate a virtualenv that was already created in $TPA_DIR/tpa-virtualenv :

```
    # Activate ansible-python ( and add command to .bashrc/.profile)
    [tpa]$ source $TPA_DIR/tpa-virtualenv/bin/activate
```

Set ANSIBLE_DIR & ANSIBLE_LOG_PATH in your environment (and .bashrc / .profile):
```
    [tpa]$ export ANSIBLE_HOME=$TPA_DIR/tpa-virtualenv
    [tpa]$ export ANSIBLE_LOG_PATH=~/ansible.log
```
Ansible creates retry files which can be used to retry commands when a playbook fails and retry_files_enabled is True (the default). This is configured in TPA_DIR/ansible.cfg and is set by default to `retry_files_save_path = ~/.ansible-retry`

Now you should be able to run ./ansible/ansible from your local copy of the TPA repository. 
The following simple tests should succeed if Ansible has been installed correctly:

```
    [tpa]$ $TPA_DIR/ansible/ansible localhost -m ping
    [tpa]$ $TPA_DIR/ansible/ansible localhost -c ssh -a "id"
```

------

### Option 2 - install from repositories

Clone the TPAexec repository

```
    [tpa]$ git clone --recursive https://github.com/2ndQuadrant/TPA
```
Set TPA_DIR and add the TPA bin directory to your path in the TPAexec user environment (and .bashrc / .profile):
```
    [tpa]$ export TPA_DIR=/path/to/TPA
    [tpa]$ export PATH=$PATH:$TPA_DIR/bin
```
Create and activate a virtualenv, to avoid installing Ansible's Python
module dependencies system-wide (highly recommended):

```
    [tpa]$ virtualenv ~/tpa-virtualenv

    # Activate ansible-python ( and add command to .bashrc/.profile)
    [tpa]$ source ~/tpa-virtualenv/bin/activate
```

Install the python dependencies into the virtualenv (including ansible:
```
    [tpa]$ pip install -r $TPA_DIR/python-requirements.txt
```
You will need Ansible 2.6 from the [2ndQuadrant/ansible repository](https://github.com/2ndQuadrant/ansible).

Clone the Ansible repository:

```
    [tpa]$ git clone --recursive https://github.com/2ndQuadrant/ansible
```

Set ANSIBLE_HOME in your environment (and .bashrc / .profile):

```
    [tpa]$ export ANSIBLE_HOME=/path/to/ansibledir
```

Ansible creates retry files which can be used to retry commands when a playbook fails and retry_files_enabled is True (the default). This is configured in TPA_DIR/ansible.cfg and is set by default to `retry_files_save_path = ~/.ansible-retry`

Now you should be able to run ./ansible/ansible from your local copy of the TPA repository. 
The following simple tests should succeed if Ansible has been installed correctly:

```
    [tpa]$ $TPA_DIR/ansible/ansible localhost -m ping
    [tpa]$ $TPA_DIR/ansible/ansible localhost -c ssh -a "id"
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


