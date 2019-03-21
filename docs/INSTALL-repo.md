# Installing TPAexec from source

This document explains how to use a copy of the TPAexec source code
repository instead of installing the tpaexec package.

Please install TPAexec from packages unless you have been given access
to the TPA source code repository and specifically advised to use it by
2ndQuadrant.

## Quickstart

```bash
[tpa]$ git clone ssh://git@git.2ndquadrant.com/products/tpa/tpaexec.git
[tpa]$ ./tpaexec/bin/tpaexec setup
[tpa]$ ./tpaexec/bin/tpaexec selftest
```

## Step-by-step

First, you must install some required system packages. (These would have
been installed automatically as dependencies if you were installing the
tpaexec package.)

```bash
# Debian or Ubuntu
[root]# apt-get install python2.7 python-pip python-virtualenv \
        pwgen openvpn

# RedHat or CentOS
[root]# yum install python python-pip python-virtualenv \
        pwgen epel-release openvpn

# MacOS X
[root]# brew tap discoteq/discoteq
[root]# brew install python@2 pwgen openvpn flock
[root]# pip install virtualenv
```

Next, clone the TPAexec repository:

```bash
[tpa]$ git clone ssh://git@git.2ndquadrant.com/products/tpa/tpaexec.git
```

We strongly recommend not cloning into ``/opt/2ndQuadrant/TPA`` so as to
avoid any conflicts if you install the TPAexec packages in future. Apart
from that, the location doesn't matter.

For TPAexec developers only: if you need to make or test changes to
2ndQuadrant Ansible (not ordinarily required), clone the repository and
set ``ANSIBLE_HOME`` in your environment (and .bashrc/.profile):

```bash
[tpa]$ git clone https://github.com/2ndQuadrant/ansible
[tpa]$ export ANSIBLE_HOME=/path/to/ansibledir
```

The remaining steps from this point onwards are the same as if you had
installed the tpaexec package.

Install the TPAexec dependencies into an isolated virtualenv:

```bash
[tpa]$ ./tpaexec/bin/tpaexec setup
```

For convenience, add tpaexec to your PATH:

```bash
# The following line can also go into ~/.bashrc or similar
[tpa]$ export PATH=$PATH:/path/to/tpaexec/bin
```

Finally, test that everything is as it should be:

```bash
[tpa]$ tpaexec selftest
```

If that command completes without any errors, your TPAexec installation
is ready for use.

## virtualenv options

By default, ``tpaexec setup`` will create a virtualenv under
``$TPA_DIR/tpa-virtualenv``, and activate it automatically whenever
``tpaexec`` is invoked.

You can run ``tpaexec setup --virtualenv /other/location`` to specify a
different location for the new virtualenv. You can also install packages
into an existing virtualenv by activating it before you invoke
``tpaexec setup``.

We strongly suggest sticking to the default virtualenv location. If you
use a different location, ``tpaexec`` cannot automatically activate the
virtualenv; you must do so yourself, for example by adding the following
line to your .bashrc (or other shell startup scripts):

```bash
source /some/virtualenv/bin/activate
```
