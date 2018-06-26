---
title: TPAexec - Detailed Installation guide
version: 1.0
date: 26/June/2018
author: Abhijit Menon-Sen
copyright-holder: 2ndQuadrant Limited
toc: true
---

# TPAexec - installation from source repository

© Copyright 2ndQuadrant, 2018. Confidential property of 2ndQuadrant; not for public release.

This document covers using TPAexec from a copy of the source code
repository instead of installing it from packages.

Please install TPAexec packages unless you have been given access to the
TPA repository and specifically advised to use it by 2ndQuadrant. If in
doubt, please contact tpa@2ndQuadrant.com.

## Clone the repository

The TPAexec packages will install TPAexec into ``/opt/2ndQuadrant/TPA``.

Please pick a different location (to avoid conflicts with future package
installations) and clone the git repository:

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

## Python environment

To use TPAexec, you will need to set up a Python environment with the
correct modules installed.

The instructions to do this are the same whether you are running from a
source checkout or from a packaged installation. Please consult the main
[installation instructions](INSTALL.md) for more.

------

[^Information Classification: Internal]: [ISP008] Information Classification Policy


