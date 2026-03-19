---
description: Installing and running TPA from a copy of the source code repository.
---


# Installing TPA from source

This document explains how to use TPA from a copy of the source code
repository.

!!! Note
      EDB customers must [install TPA from packages](INSTALL.md) in
      order to receive EDB support for the software.

To run TPA from source, you must install all of the dependencies
(e.g., Python 3.12+) that the packages would handle for you, or download
the source and [run TPA in a Docker container](INSTALL-docker.md).
(Either way will work fine on Linux and macOS.)

## Prerequisites

Before installing TPA from source, ensure that `git` is available on your system.

You must also have a **Python 3.12** interpreter, including the `pip` and `venv` modules, present on the TPA controller host. 

- For **RHEL 9**, you may need to enable the CodeReady Linux Builder (CRB) repository to install necessary build dependencies.
- For **SLES**, ensure the Python 3.12 module is enabled.
- If your operating system repositories do not provide Python 3.12, we recommend using [pyenv](https://github.com/pyenv/pyenv) to install it.

!!! Note

      Legacy dependencies such as `openvpn` and `patch` are no longer required for standard TPA installations and have been removed from these instructions.


## Clone and setup

With prerequisites installed, you can now clone the repository.

```shell
git clone https://github.com/enterprisedb/tpa.git ~/tpa
```

This creates a `tpa` directory in your home directory.

If you prefer to checkout with ssh use:

```shell
git clone ssh://git@github.com/EnterpriseDB/tpa.git ~/tpa
```

Add the bin directory, found within in your newly created clone, to your path with:

```shell
export PATH=$PATH:$HOME/tpa/bin
```

Add this line to your `.bashrc` file (or other profile file for your preferred shell).

You can now create a working tpa environment by running:

```shell
tpaexec setup
```

This will create the Python virtual environment that TPA will use in future. All needed packages are installed in this environment. To test this configured correctly, run the following:

```shell
tpaexec selftest
```

You now have tpaexec installed.

## Dependencies

### Python 3.12+

TPA requires Python 3.12 or later, available on most
modern distributions. If you don't have it, you can use
[pyenv](https://github.com/pyenv/pyenv) to install any version of Python
you like without affecting the system packages.

```shell
# First, install pyenv and activate it in ~/.bashrc
# See https://github.com/pyenv/pyenv#installation
# (e.g., `brew install pyenv` on MacOS X)

pyenv install 3.12.0
```
```output
Downloading Python-3.12.0.tar.xz...
-> https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tar.xz
Installing Python-3.12.0...
Installed Python-3.12.0 to /home/ams/.pyenv/versions/3.12.0
```
```shell
pyenv local 3.12.0
pyenv version
```
```output
3.12.0 (set by /home/ams/pyenv/.python-version)
```
```shell
pyenv which python3
```
```output
/home/ams/.pyenv/versions/3.12.0/bin/python3
```
```shell
python3 --version
```
```output
3.12.0
```

If you were not already using pyenv, please remember to add `pyenv` to
your PATH in .bashrc and call `eval "$(pyenv init -)"` as described in
the [pyenv documentation](https://github.com/pyenv/pyenv#installation).

### Virtual environment options

By default, `tpaexec setup` will use the builtin Python 3 `-m venv`
to create a venv under `$TPA_DIR/tpa-venv`, and activate it
automatically whenever `tpaexec` is invoked.

You can run `tpaexec setup --venv /other/location` to specify a
different location for the new venv.

We strongly suggest sticking to the default venv location. If you use a
different location, you must also set the environment variable TPA_VENV
to its location, for example by adding the following line to your
.bashrc (or other shell startup scripts):

```shell
export TPA_VENV="/other/location"
```
