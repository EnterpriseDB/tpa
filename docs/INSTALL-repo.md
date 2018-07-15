---
title: TPAexec - Installation guide from repo
version: 1.2
date: 28/June/2018
author: Abhijit Menon-Sen, Craig Alsop
copyright-holder: 2ndQuadrant Limited
toc: true
---

TPAexec installation from source repository
===========================================

© Copyright 2ndQuadrant, 2014-2018. Confidential property of 2ndQuadrant; not for public release.

This document covers using TPAexec from a copy of the source code
repository instead of installing it from packages.

Please install TPAexec packages unless you have been given access to the
TPA repository and specifically advised to use it by 2ndQuadrant. If in
doubt, please contact tpa@2ndQuadrant.com.

## Quickstart

    [tpa]$ git clone https://github.com/2ndQuadrant/TPA
    [tpa]$ ./TPA/bin/tpaexec setup
    [tpa]$ ./TPA/bin/tpaexec selftest

## Step-by-step installation

First, install some required system packages:

    # Debian or Ubuntu
    [root]# apt-get install python2.7 python-pip python-virtualenv \
            pwgen openvpn
    
    # RedHat or CentOS
    [root]# yum install python python-pip python-virtualenv \
            pwgen epel-release openvpn
            
    # Mac
        [brew or port] install pwgen
        [brew or port] install openvpn

Then clone the TPA repository:

    [tpa]$ git clone https://github.com/2ndQuadrant/TPA

We strongly recommend not cloning into ``/opt/2ndQuadrant/TPA`` so as to
avoid any conflicts if you install the TPAexec packages in future. Apart
from that, the location doesn't matter.

For TPAexec developers only: if you need to make or test changes to
2ndQuadrant Ansible (not ordinarily required), clone the repository and
set ``ANSIBLE_HOME`` in your environment (and .bashrc/.profile):

    [tpa]$ git clone https://github.com/2ndQuadrant/ansible
    [tpa]$ export ANSIBLE_HOME=/path/to/ansibledir

Next, install the TPAexec dependencies into an isolated virtualenv:

    [tpa]$ ./TPA/bin/tpaexec setup

For convenience, add tpaexec to your PATH:

    # The following line can also go into ~/.bashrc or similar
    [tpa]$ export PATH=$PATH:/path/to/TPA/bin

Finally, test that everything is as it should be:

    [tpa]$ tpaexec selftest

If that command completes without any errors, your TPAexec installation
is ready for use.

## virtualenv options

By default, ``tpaexec setup`` will create a virtualenv under
``$TPA_DIR/tpa-virtualenv``, and activate it automatically whenever
``tpaexec`` is invoked.

You can run ``tpaexec setup --virtualenv /other/location`` to specify a
different location for the new virtualenv. You can also install packages
into an existing virtualenv by activating it before you invoke ``tpaexec
setup``.

We strongly suggest sticking to the default virtualenv when possible. If
you use a different location, ``tpaexec`` cannot automatically activate
the virtualenv, so it is your responsibility to do so before invoking
``tpaexec``. For example, you could add the following to your shell
startup scripts (i.e., .bashrc/.profile):

    source /some/virtualenv/bin/activate

## Help

Write to tpa@2ndQuadrant.com for help.

------

[^Information Classification: Internal]: [ISP008] Information Classification Policy

