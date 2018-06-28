---
title: TPAexec - Installation guide from repo
version: 1.2
date: 28/June/2018
author: Abhijit Menon-Sen, Craig Alsop
copyright-holder: 2ndQuadrant Limited
toc: true
---

# TPAexec - installation from source repository

© Copyright 2ndQuadrant, 2014-2018. Confidential property of 2ndQuadrant; not for public release.

This document covers using TPAexec from a copy of the source code
repository instead of installing it from packages.

Please install TPAexec packages unless you have been given access to the
TPA repository and specifically advised to use it by 2ndQuadrant. If in
doubt, please contact tpa@2ndQuadrant.com.

## Clone the TPA repository

The TPAexec packages install TPAexec into ``/opt/2ndQuadrant/TPA``.

As you have decided not to use the packages please pick a different location (to avoid conflicts with future package installations) and clone the git repository:

```
[tpa]$ git clone https://github.com/2ndQuadrant/TPA
```

## Install system packages

Whereas the TPAexec package installs a number of packages as
dependencies by default, you must install these by hand as follows:

    # Debian or Ubuntu
    [root]# apt-get install python2.7 python-pip python-virtualenv \
            pwgen openvpn
    
    # RedHat or CentOS
    [root]# yum install python python-pip python-virtualenv \
            pwgen epel-release openvpn
            
    # Mac
        [brew or port] install pwgen
        [brew or port] install openvpn

## Python environment

To use TPAexec, you will need to set up a Python environment with the
correct modules installed.

Set TPA_DIR and add the TPA bin directory to your path in the TPAexec user environment (and .bashrc / .profile):
```
    [tpa]$ export TPA_DIR=/path/to/TPA
    [tpa]$ export PATH=$PATH:$TPA_DIR/bin
```
Create and activate a virtualenv, to avoid installing Ansible's Python module dependencies system-wide (highly recommended):

```
    [tpa]$ virtualenv ~/tpa-virtualenv

    # Activate ansible-python ( and add command to .bashrc/.profile)
    [tpa]$ source ~/tpa-virtualenv/bin/activate
```

Install the python dependencies into the virtualenv (including ansible:
```
    # upgrade pip
    [tpa]$ pip install --upgrade pip
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

## Verification

Once you're done with all of the above steps, run the following command
to verify your local installation:

    [tpa]$ tpaexec selftest

If that command completes without any errors, your TPAexec installation
is ready for use.

SELinux known issue
-------------------

A bug with virtualenv on some versions of a RHEL derivative host (RHEL and CentOS) can mean this error is generated from ansible:
"Aborting, target uses selinux but python bindings (libselinux-python) aren't installed!"

A workaround is to copy selinux package into the virtual environment: 

```
    [tpa]$ cp -rp /usr/lib64/python2.7/site-packages/selinux \
    ~/tpa-virtualenv/lib/python2.7/site-packages
```

## Help

Write to tpa@2ndQuadrant.com for help.

------

[^Information Classification: Internal]: [ISP008] Information Classification Policy

