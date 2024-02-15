# TPA installation

To use TPA, you need to install from packages or source and run the
`tpaexec setup` command. If you have an EDB subscription plan, and therefore have
access to the EDB repositories, follow these instructions to install TPA packages.

To install TPA from source, see
[Installing from source](INSTALL-repo.md).

See [Distribution support](distributions.md) for information
about the platforms that are supported.

!!! Info
    Make absolutely sure that your system has the correct
    date and time set. Various operations will fail otherwise. We
    recommend you use a network time, for example, `sudo ntpdate
    pool.ntp.org`.

## Quick start

To obtain your token, log in to [EDB Repos 2.0](https://www.enterprisedb.com/repos-downloads).
Then execute the following command, substituting
your token for `<your-token>`. Replace `<your-plan>` with
one of the following according to the EDB plan you're subscribed to:
`enterprise`, `standard`, `community360`, or `postgres_distributed`.

#### Add repository and install TPA on Debian or Ubuntu
```bash
curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/<your-plan>/setup.deb.sh' | sudo -E bash
sudo apt-get install tpaexec
```

#### Add repository and install TPA on RHEL, Rocky, AlmaLinux, or Oracle Linux
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

More detailed explanations of each step follow.

## Where to install TPA

As long as you're using a supported platform, you can install and run TPA
from your workstation. This approach is fine for learning, local testing, or
demonstration purposes. if you want to perform a complete deployment on your
own workstation, TPA supports [deploying to Docker containers](platform-docker.md).

For production use, we recommend running TPA on a dedicated persistent
virtual machine. We recommend this because it ensures that the cluster
directories are retained and available to your team for future cluster
management or update. It also means you have to update only one copy of
TPA and you need to provide network access only from a single TPA host
to the target instances.

## Installing TPA packages

To install TPA, you must first subscribe to an EDB repository that
provides it. The preferred source for repositories is EDB Repos 2.0.

To obtain your token, log in to [EDB Repos 2.0](https://www.enterprisedb.com/repos-downloads).
Then execute the following command, substituting
your token for `<your-token>`. Replace `<your-plan>` with
one of the following according to the EDB plan you're subscribed to:
`enterprise`, `standard`, `community360`, or `postgres_distributed`.

#### Add repository on Debian or Ubuntu
```bash
curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/<your-plan>/setup.deb.sh' | sudo -E bash

```

#### Add repository on RHEL, Rocky, AlmaLinux or Oracle Linux
```bash
curl -1sLf 'https://downloads.enterprisedb.com/<your-token>/<your-plan>/setup.rpm.sh' | sudo -E bash
```

Alternatively, you can obtain TPA from the legacy 2ndQuadrant
repository. To do so, log in to the EDB Customer Support Portal and
subscribe to the [products/tpa/release repository](https://techsupport.enterprisedb.com/software_subscriptions/add/products/tpa/)
by adding a subscription under **Support/Software/Subscriptions**.
Then follow the instructions to enable the repository on your system.

Once you have enabled one of these repositories, you can install TPA
as follows.

#### Install on Debian or Ubuntu
```bash
sudo apt-get install tpaexec
```
#### Install on RHEL, Rocky, AlmaLinux, or Oracle Linux
```bash
sudo yum install tpaexec
```

This command installs TPA into `/opt/EDB/TPA`. It also
ensures that other required packages (such as Python 3.9 or later) are
installed.

We mention `sudo` here only to indicate the commands that need root
privileges. You can use any other means to run the commands as root.

## Setting up the TPA Python environment

Next, run `tpaexec setup` to create an isolated Python environment and
install the correct versions of all required modules.

!!! Note
    On Ubuntu versions prior to 20.04, use `sudo -H tpaexec setup`
    to avoid subsequent permission errors during `tpaexec configure`.

```bash
sudo /opt/EDB/TPA/bin/tpaexec setup
```

You must run this command as root because it writes to `/opt/EDB/TPA`,
but the process doesn't affect any system-wide Python modules you
have installed (including Ansible).

Add `/opt/EDB/TPA/bin` to the `PATH` of the user who
normally runs `tpaexec` commands. For example, you can add this to
your `.bashrc` or equivalent shell configuration file:

```bash
export PATH=$PATH:/opt/EDB/TPA/bin
```

## Installing TPA without internet or network access (air-gapped)

You can install TPA onto a server that can't
access either the EDB repositories, a Python package index, or both.
For information on how to use TPA in such an environment, see
[Managing clusters in a disconnected or air-gapped
environment](air-gapped.md).

### Downloading TPA packages

If you can't access the EDB repositories directly from the server on
which you need to install TPA, you can download the packages from an
internet-connected machine and transfer them. There are several ways to
achieve this.

If your internet-connected machine uses the same operating system as the
target, we recommend using `yumdownloader` (RHEL-like) or `apt download`
(Debian-like) to download the packages.

If this approach isn't possible, contact EDB Support, which can provide
you with a download link or instructions appropriate to your
subscription.

### Installing without access to a Python package index

When you run `tpaexec setup`, it ordinarily downloads the Python
packages from a Python package index. Unless your environment provides a
different index, the default is the official [PyPI](https://pypi.org). If
no package index is available, install the `tpaexec-deps`
package in the same way you installed tpaexec. The `tpaexec-deps`
package (available from the same repository as tpaexec) bundles
everything that you would have downloaded, so that they can be
installed without network access. Install the package before you
run `tpaexec setup`, and the bundled copies are used automatically.

## Verifying your TPA installation

After completing the installation,
verify your local installation:

```bash
tpaexec selftest
```

If this command completes without any errors, your TPA installation
is ready for use.

## Upgrading TPA

To upgrade to a later release of TPA, you must:

1. Install the latest `tpaexec` package.
2. Install the latest `tpaexec-deps` package (if required; see [Installing without access to a Python package index](#installing-without-access-to-a-python-package-index)).
3. Run `tpaexec setup` again.

If you subscribed to the TPA package repository,
running `apt-get update && apt-get upgrade` or `yum update`
installs the latest available versions of these packages. If not,
you can install the packages by any means available.

We recommend that you run `tpaexec setup` again whenever a new version
of `tpaexec` is installed. Some new releases might not strictly require
this, but others can't work without it.

## Ansible versions

TPA uses Ansible version 8 by default (ansible-core 2.15). You can use
2ndQuadrant Ansible version 2.9 by passing the `--use-2q-ansible`
option to `tpaexec setup`, or a different version of community Ansible
by passing the `--ansible-version` option with a version number
argument. The available versions are `2.9`, `8`, and `9`.

Ansible 2.9 is now deprecated in TPA and support for it will be removed
in a future version. If you are using `--skip-tags`, you need to
continue to use 2ndQuadrant Ansible 2.9 because of the changes in the
behaviour of this option in community Ansible; an alternative means of
skipping tasks will be provided in a future TPA version, before support
for 2ndQuadrant ansible is removed.

Support for Ansible 9 is experimental. It requires Python 3.10 or
greater, so if you have edb-python 3.9 installed, you must explicitly
set your python version when running `tpaexec setup`:

```bash
PYTHON=/usr/bin/python3.10 tpaexec setup --ansible-version 9
```
