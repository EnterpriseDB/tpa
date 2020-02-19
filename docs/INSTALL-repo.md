# Installing TPAexec from source

This document explains how to use a copy of the TPAexec source code
repository instead of installing the tpaexec package.

Please install TPAexec from packages unless you have been given access
to the TPA source code repository and specifically advised to use it by
2ndQuadrant.

## Quickstart

```bash
$ git clone ssh://git@git.2ndquadrant.com/products/tpa/tpaexec.git
$ ./tpaexec/bin/tpaexec setup
$ ./tpaexec/bin/tpaexec selftest
```

## Step-by-step

First, you must install some required system packages. (These would have
been installed automatically as dependencies if you were installing the
tpaexec package.)

```bash
# Debian (python3.7) or Ubuntu (python3.6)
$ sudo apt-get install python3.7 python3-pip python3-venv \
      pwgen openvpn

# RedHat or CentOS (python3 for RHEL7, python36 for RHEL8)
$ sudo yum install python36 python3-pip \
      pwgen epel-release openvpn

# MacOS X
$ sudo brew tap discoteq/discoteq
$ sudo brew install python@3 pwgen openvpn flock
```

(We mention ``sudo`` here only to indicate which commands need root
privileges. You may use any other means to run the commands as root.)

Next, clone the TPAexec repository:

```bash
$ git clone ssh://git@git.2ndquadrant.com/products/tpa/tpaexec.git
```

We strongly recommend not cloning into ``/opt/2ndQuadrant/TPA`` so as to
avoid any conflicts if you install the TPAexec packages in future. Apart
from that, the location doesn't matter.

For TPAexec developers only: if you need to make or test changes to
2ndQuadrant Ansible (not ordinarily required), clone the repository and
set ``ANSIBLE_HOME`` in your environment (and .bashrc/.profile):

```bash
$ git clone https://github.com/2ndQuadrant/ansible
$ export ANSIBLE_HOME=/path/to/ansibledir
```

The remaining steps from this point onwards are the same as if you had
installed the tpaexec package.

The following command will create an isolated Python environment and
install the TPAexec dependencies:

```bash
$ ./tpaexec/bin/tpaexec setup
```

For convenience, add tpaexec to your PATH:

```bash
# The following line can also go into ~/.bashrc or similar
$ export PATH=$PATH:/path/to/tpaexec/bin
```

Finally, test that everything is as it should be:

```bash
$ tpaexec selftest
```

If that command completes without any errors, your TPAexec installation
is ready for use.

## Virtual environment options

By default, ``tpaexec setup`` will use the builtin Python 3 ``-m venv``
to create a venv under ``$TPA_DIR/tpa-venv``, and activate it
automatically whenever ``tpaexec`` is invoked.

You can run ``tpaexec setup --venv /other/location`` to specify a
different location for the new venv.

We strongly suggest sticking to the default venv location. If you use a
different location, ``tpaexec`` cannot automatically activate the venv;
you must do so yourself, for example by adding the following line to
your .bashrc (or other shell startup scripts):

```bash
source /some/venv/bin/activate
```
