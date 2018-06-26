---
title: TPAexec - Installation guide
version: 1.5
date: 26/June/2018
author: Craig Alsop, Abhijit Menon-Sen
copyright-holder: 2ndQuadrant Limited
toc: true
---

# TPAexec - Installation guide

© Copyright 2ndQuadrant. Confidential, not for public release.

## Overview

To use TPAexec, you will need:

1. The TPAexec source code itself

2. Python 2.7 and some Python modules

3. A few other programs that TPAexec uses

This document explains how to set up these things and start using
TPAexec.

Commands run as root will be shown starting with a **[root]#** and commands run as tpa user will be shown starting with a **[tpa]$**

## What time is it?

Please make absolutely sure that your system has the correct date and
time set, because various things will fail otherwise. For example:

    [root]# ntpdate pool.ntp.org

## TPAexec

TPAexec packages are available from the 2ndQuadrant internal package
repository. These instructions assume that you either have access to
this repository, or have been given a copy of the package separately.

You can install the tpaexec package as follows:

    # Debian or Ubuntu
    [root]# apt-get install tpaexec-<version-number.os-type>_all.deb

    # RedHat or CentOS
    [root]# yum install tpaexec-<version-number>.noarch.rpm

This will install TPAexec into ``/opt/2ndQuadrant/TPA``.

Installing the TPAexec package will also ensure that other required
packages (such as Python 2.7) are installed.

(If you have been given access to the TPA source code repository and
specifically advised to use it, please see the
[source installation instructions](INSTALL-repo.md) instead.)

## Python environment

At this point, Python 2.7, pip, and virtualenv should be available on
your system. Now you need to setup a Python environment to install the
Python modules that TPAexec needs.

The procedure below installs these modules into an isolated virtualenv,
which we strongly recommend. It avoids interference with any system-wide
Python modules you have installed, and ensures that you have the correct
versions of the modules. (For the same reason, we also do not recommend
using OS packages to install these modules.)

First, create the virtualenv, activate and install the packages using the install script.

    # Create a virtualenv and install the pip modules (including ansible).
    [root]# /opt/2ndQuadrant/TPA/misc/tpa-virtualenv-install.sh

Now, as a non-root user, add the following to your .bashrc or
.profile (or equivalent shell startup configuration):

    [tpa]$ export PATH=$PATH:/opt/2ndQuadrant/TPA/bin
    [tpa]$ export ANSIBLE_HOME=/opt/2ndQuadrant/TPA/tpa-virtualenv

To use TPAexec, you must also activate the virtualenv you created above.
You may run this command either by hand (when you need to use TPAexec),
or add the command to your .bashrc:

    # Activate virtualenv
    [tpa]$ source $TPA_DIR/tpa-virtualenv/bin/activate

## Verification

Once you're done with all of the above steps, run the following command
to verify your local installation:

    [tpa]$ tpaexec selftest

If that command completes without any errors, your TPAexec installation
is ready for use.

## Help

Write to tpa@2ndQuadrant.com for help.

------

[^Information Classification: Internal]: [ISP008] Information Classification Policy


