---
description: Installing TPA packages and setting up the Python environment.
---

# TPA installation

To use TPA, you need to install from packages or source and run the
`tpaexec setup` command. This document explains how to install TPA
packages. If you have an EDB subscription plan, and therefore have
access to the EDB repositories, you should follow these instructions. To
install TPA from source, please refer to
[Installing TPA from Source](INSTALL-repo.md).

See [Distribution support](distributions.md) for information
on what platforms are supported.

!!! Info
    Please make absolutely sure that your system has the correct
    date and time set, because various things will fail otherwise. We
    recommend you use a network time, for example `sudo ntpdate
    pool.ntp.org`

## Quickstart

Login to [EDB Repos 2.0](https://www.enterprisedb.com/repos-downloads)
to obtain your token. Then execute the following command, substituting
your token for `<your-token>` and replacing `<your-plan>` with
one of the following according to which EDB plan you are subscribed:
`enterprise`, `standard`, `community360`, `postgres_distributed`.

#### Add repository and install TPA on Debian or Ubuntu
```bash
curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/<your-plan>/setup.deb.sh' | sudo -E bash
sudo apt-get install tpaexec
```

#### Add repository and install TPA on RHEL, Rocky, AlmaLinux or Oracle Linux
```bash
curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/<your-plan>/setup.rpm.sh' | sudo -E bash
sudo yum install tpaexec
```

#### Install additional dependencies
```bash
sudo /opt/EDB/TPA/bin/tpaexec setup
```

#### Verify installation (run as a normal user)
```bash
/opt/EDB/TPA/bin/tpaexec selftest
```

More detailed explanations of each step are given below.

## Where to install TPA

As long as you are using a supported platform, TPA can be installed and
run from your workstation. This is fine for learning, local testing or
demonstration purposes. TPA supports [deploying to Docker containers](platform-docker.md)
should you wish to perform a complete deployment on your own workstation.

For production use, we recommend running TPA on a dedicated, persistent
virtual machine. We recommend this because it ensures that the cluster
directories are retained and available to your team for future cluster
management or update. It also means you only have to update one copy of
TPA and you only need to provide network access from a single TPA host
to the target instances.
## Installing TPA packages

To install TPA, you must first subscribe to an EDB repository that
provides it. The preferred source for repositories is EDB Repos 2.0.

Login to [EDB Repos 2.0](https://www.enterprisedb.com/repos-downloads)
to obtain your token. Then execute the following command, substituting
your token for `<your-token>` and replacing `<your-plan>` with
one of the following according to which EDB plan you are subscribed:
`enterprise`, `standard`, `community360`, `postgres_distributed`.

#### Add repository on Debian or Ubuntu
```bash
curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/<your-plan>/setup.deb.sh' | sudo -E bash

```

#### Add repository on RHEL, Rocky, AlmaLinux or Oracle Linux
```bash
curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/<your-plan>/setup.rpm.sh' | sudo -E bash
```

Alternatively, you may obtain TPA from the legacy 2ndQuadrant
repository. To do so, login to the EDB Customer Support Portal and
subscribe to the ["products/tpa/release" repository](https://techsupport.enterprisedb.com/software_subscriptions/add/products/tpa/)
by adding a subscription under Support/Software/Subscriptions,
and following the instructions to enable the repository on your system.

Once you have enabled one of these repositories, you may install TPA
as follows:

#### Install on Debian or Ubuntu
```bash
sudo apt-get install tpaexec
```
#### Install on RHEL, Rocky, AlmaLinux or Oracle Linux
```bash
sudo yum install tpaexec
```

This will install TPA into `/opt/EDB/TPA`. It will also
ensure that other required packages (e.g., Python 3.9 or later) are
installed.

We mention `sudo` here only to indicate which commands need root
privileges. You may use any other means to run the commands as root.

## Setting up the TPA Python environment

Next, run `tpaexec setup` to create an isolated Python environment and
install the correct versions of all required modules.

!!! Note
    On Ubuntu versions prior to 20.04, please use `sudo -H tpaexec setup`
    to avoid subsequent permission errors during `tpaexec configure`

```bash
sudo /opt/EDB/TPA/bin/tpaexec setup
```

You must run this as root because it writes to `/opt/EDB/TPA`,
but the process will not affect any system-wide Python modules you may
have installed (including Ansible).

Add `/opt/EDB/TPA/bin` to the `PATH` of the user who will
normally run `tpaexec` commands. For example, you could add this to
your .bashrc or equivalent shell configuration file:

```bash
export PATH=$PATH:/opt/EDB/TPA/bin
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

Alternatively, you can download packages for any platform from your 
browser by visiting [EDB Repos](https://www.enterprisedb.com/repos) and
selecting either 'Enterprise', 'Standard' or 'Community 360' under the 
heading 'Download EDB software packages from your browser'. 
To install TPA you need these packages:

* tpaexec
* tpaexec-deps
* edb-python39

Once you have transferred the downloaded packages to the target server,
you must install them using the appropriate tool for your platform.

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

## Verifying your TPA installation

Once you're done with all of the above steps, run the following command
to verify your local installation:

```bash
tpaexec selftest
```

If that command completes without any errors, your TPA installation
is ready for use.

## Upgrading TPA

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

## Ansible versions

TPA uses Ansible version 8 by default (ansible-core 2.15).

TPA has experimental support for Ansible 9 (ansible-core 2.16),
which can be specified using the `--ansible-version` argument to
`tpaexec setup`. It requires Python 3.10 or greater, so if you have
edb-python 3.9 installed, you must explicitly set your python version
when running `tpaexec setup`:

```bash
PYTHON=/usr/bin/python3.10 tpaexec setup --ansible-version 9
```
