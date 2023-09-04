# Installing TPA from source

This document explains how to use TPA from a copy of the source code
repository.

!!! Note 
      EDB customers must [install TPA from packages](INSTALL.md) in
      order to receive EDB support for the software.

To run TPA from source, you must install all of the dependencies
(e.g., Python 3.6+) that the packages would handle for you, or download
the source and [run TPA in a Docker container](INSTALL-docker.md).
(Either way will work fine on Linux and macOS.)

## Quickstart

First, you must install the various dependencies that would have been
installed automatically along with the TPA packages. (You can use
something other than `sudo` to run these commands as root, if you
prefer.)


```bash
# Debian or Ubuntu 
$ sudo apt-get install python3 python3-pip python3-venv \
      git openvpn patch

# RedHat, Rocky or AlmaLinux (python3 for RHEL7, python36 for RHEL8)
$ sudo yum install python36 python3-pip \
      epel-release git openvpn patch

# MacOS X
$ brew tap discoteq/discoteq
$ brew install python@3 openvpn flock coreutils gpatch git
```

Next, install TPA itself:

```bash
$ git clone ssh://git@github.com/EnterpriseDB/tpaexec.git
$ ./tpaexec/bin/tpaexec setup
$ ./tpaexec/bin/tpaexec selftest
```

## Step-by-step

Install the various dependencies as described above.

If your system does not have Python 3.6+ packages, you can use `pyenv`
to install a more recent Python in your home directory (see below), or
you can [run TPA in a Docker container](INSTALL-docker.md).

Next, clone the TPA repository into, say, `~/tpaexec`. (It doesn't
matter where you put it, but don't use `/opt/EDB/TPA` or
`/opt/2ndQuadrant/TPA`, to avoid conflicts if you install the TPA
packages in future.)

```bash
$ git clone ssh://git@github.com/EnterpriseDB/tpaexec.git ~/tpaexec
```

(If you're installing from source, please clone the repository instead
of downloading an archive of the source.)

The remaining steps are the same as if you had installed the package.

```bash
# Add tpaexec to your PATH for convenience
# (Put this in your ~/.bashrc too)
$ export PATH=$PATH:$HOME/tpaexec/bin

$ tpaexec setup
$ tpaexec selftest
```

If the self-test completes without any errors, your TPA installation
is ready for use.

## Python 3.6+

TPA requires Python 3.6 or later, available on most
modern distributions. If you don't have it, you can use
[pyenv](https://github.com/pyenv/pyenv) to install any version of Python
you like without affecting the system packages.

```bash
# First, install pyenv and activate it in ~/.bashrc
# See https://github.com/pyenv/pyenv#installation
# (e.g., `brew install pyenv` on MacOS X)

$ pyenv install 3.9.0
Downloading Python-3.9.0.tar.xz...
-> https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tar.xz
Installing Python-3.9.0...
Installed Python-3.9.0 to /home/ams/.pyenv/versions/3.9.0

$ pyenv local 3.9.0
$ pyenv version
3.9.0 (set by /home/ams/pyenv/.python-version)

$ pyenv which python3
/home/ams/.pyenv/versions/3.9.0/bin/python3
$ python3 --version
3.9.0
```

If you were not already using pyenv, please remember to add `pyenv` to
your PATH in .bashrc and call `eval "$(pyenv init -)"` as described in
the [pyenv documentation](https://github.com/pyenv/pyenv#installation).

## Virtual environment options

By default, `tpaexec setup` will use the builtin Python 3 `-m venv`
to create a venv under `$TPA_DIR/tpa-venv`, and activate it
automatically whenever `tpaexec` is invoked.

You can run `tpaexec setup --venv /other/location` to specify a
different location for the new venv.

We strongly suggest sticking to the default venv location. If you use a
different location, you must also set the environment variable TPA_VENV
to its location, for example by adding the following line to your
.bashrc (or other shell startup scripts):

```bash
export TPA_VENV="/other/location"
```
