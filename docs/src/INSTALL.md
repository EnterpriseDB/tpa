# TPA installation

To use TPA, you need to install tpaexec and run the `tpaexec setup`
command. This document explains how to install TPA packages.

TPA packages are available to prospects (for a 60 day trial), EDB
customers with a valid Extreme HA subscription, or by prior arrangement.
Please contact your account manager to request access.

## Distribution support

We publish TPA packages for Debian 10 (buster), Ubuntu 22.04 (jammy), Ubuntu 20.04
(focal), Ubuntu 18.04 (bionic), RHEL/CentOS 7.x and 8.x, Rocky 8.x and AlmaLinux 8.x. These
distributions provide a usable Python 3.6+ environment out of the box,
which TPA requires. However, TPA supports a wider range of
[distributions on target instances](distributions.md).

## Quickstart

Login to [EDB Repos 2.0](https://www.enterprisedb.com/repos-downloads)
to obtain your token. Then execute the following command, substituting
your token for `<your-token>`.

```bash
# Add repository (Debian, Ubuntu)
$ curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/postgres_distributed/setup.deb.sh' | sudo -E bash

# Add repository (RedHat, Rocky or AlmaLinux)
$ curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/postgres_distributed/setup.rpm.sh' | sudo -E bash
```

Then run the following commands:

```bash
# Install packages (Debian, Ubuntu)
$ sudo apt-get install tpaexec

# Install packages (RedHat, Rocky or AlmaLinux)
$ sudo yum install tpaexec

# Install additional dependencies
$ sudo /opt/EDB/TPA/bin/tpaexec setup

# Verify installation (run as a normal user)
$ /opt/EDB/TPA/bin/tpaexec selftest
```

More detailed explanations are given below.

## What time is it?

Please make absolutely sure that your system has the correct date and
time set, because various things will fail otherwise. For example:

```bash
$ sudo ntpdate pool.ntp.org
```

## Packages

To install TPA, you must first subscribe to an EDB repository that
provides it. The preferred source for repositories is EDB Repos 2.0.

Login to [EDB Repos 2.0](https://www.enterprisedb.com/repos-downloads)
to obtain your token. Then execute the following command, substituting
your token for `<your-token>`.

```bash
# Debian or Ubuntu
$ curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/postgres_distributed/setup.deb.sh' | sudo -E bash

# RedHat, Rocky or AlmaLinux
$ curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/postgres_distributed/setup.rpm.sh' | sudo -E bash
```

Alternatively, you may obtain TPA from the legacy 2ndQuadrant
repository. To do so, login to the EDB Customer Support Portal and
subscribe to the ["products/tpa/release" repository](https://techsupport.enterprisedb.com/software_subscriptions/add/products/tpa/)
by adding a subscription under Support/Software/Subscriptions,
and following the instructions to enable the repository on your system.

Once you have enabled one of these repositories, you may install TPA
as follows:

```bash
# Debian or Ubuntu
$ sudo apt-get install tpaexec

# RedHat, Rocky or AlmaLinux
$ sudo yum install tpaexec
```

This will install TPA into `/opt/EDB/TPA`. It will also
ensure that other required packages (e.g., Python 3.6 or later) are
installed.

We mention `sudo` here only to indicate which commands need root
privileges. You may use any other means to run the commands as root.

## Python environment

Next, run `tpaexec setup` to create an isolated Python environment and
install the correct versions of all required modules.

!!! Note
    On Ubuntu versions prior to 20.04, please use `sudo -H tpaexec setup`
    (to avoid subsequent permission errors during `tpaexec configure`)

```bash
$ sudo /opt/EDB/TPA/bin/tpaexec setup
```

You must run this as root because it writes to `/opt/EDB/TPA`,
but the process will not affect any system-wide Python modules you may
have installed (including Ansible).

Add `/opt/EDB/TPA/bin` to the `PATH` of the user who will
normally run `tpaexec` commands. For example, you could add this to
your .bashrc or equivalent shell configuration file:

```bash
$ export PATH=$PATH:/opt/EDB/TPA/bin
```

## Installing TPA without internet or network access (air-gapped)

This section describes how to install TPA onto a server which cannot
access either the EDB repositories, a Python package index, or both.
For information on how to use TPA in such an environment, please see
[Managing clusters in a disconnected or air-gapped
environment](air-gapped.md)

### Downloading TPA packages

If you cannot access the EDB repositories directly from the server on
which you need to install TPA, you can download the packages from an
internet-connected machine and transfer them. There are several ways to
achieve this.

If your internet-connected machine uses the same operating system as the
target, we recommend using `yumdownloader` (RHEL-like) or `apt download`
(Debian-like) to download the packages.

If this is not possible, please contact EDB support and we will provide
you with a download link or instructions appropriate to your
subscription.

### Installing without access to a Python package index

When you run `tpaexec setup`, it will ordinarily download the Python
packages from a Python package index. Unless your environment provides a
different index the default is the official [PyPI](https://pypi.org). If
no package index is available, you should install the `tpaexec-deps`
package in the same way your installed `tpaexec`. The `tpaexec-deps`
package (available from the same repository as tpaexec) bundles
everything that would have been downloaded, so that they can be
installed without network access. Just install the package before you
run `tpaexec setup` and the bundled copies will be used automatically.

## Verification

Once you're done with all of the above steps, run the following command
to verify your local installation:

```bash
$ tpaexec selftest
```

If that command completes without any errors, your TPA installation
is ready for use.

## Upgrading

To upgrade to a later release of TPA, you must:

1. Install the latest `tpaexec` package
2. Install the latest `tpaexec-deps` package (if required; see above)
3. Run `tpaexec setup` again

If you have subscribed to the TPA package repository as described
above, running `apt-get update && apt-get upgrade` or `yum update`
should install the latest available versions of these packages. If not,
you can install the packages by any means available.

We recommend that you run `tpaexec setup` again whenever a new version
of `tpaexec` is installed. Some new releases may not strictly require
this, but others will not work without it.

## Ansible community support

TPA now supports ansible community, you may choose to use it by
using `--use-community-ansible` option during `tpaexec setup`, default
will be to use the legacy 2ndQuadrant/ansible fork. This will change in
a future release, support for 2ndQuadrant/ansible will be dropped and
community ansible will become the new default.

notable difference:
- change the `--skip-flags` options to community behavior where a
task will be skipped if part of the list given to the `--skip-tags`
option even if it is also tagged with special tag `always`.
TPA expects all tasks tagged with `always` to be run to ensure
a complete deployment, therefor `--skip-tags` should not be used when
using community ansible.
