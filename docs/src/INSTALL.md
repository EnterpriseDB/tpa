# TPAexec installation

To use TPAexec, you need to install tpaexec and run the `tpaexec setup`
command. This document explains how to install TPAexec packages.

TPAexec packages are available to EnterpriseDB/2ndQuadrant customers by
prior arrangement. Please contact your account manager to request
access.

We publish TPAexec packages for Debian 10 (buster), Ubuntu 20.04
(focal), Ubuntu 18.04 (bionic), RHEL/CentOS 7.x and 8.x, Rocky 8.x and AlmaLinux 8.x. These
distributions provide a usable Python 3.6+ environment out of the box,
which TPAexec requires. (However, TPAexec supports a wider range of
[distributions on target instances](distributions.md).)

## Quickstart

First, [subscribe to the TPAexec package repository](https://techsupport.enterprisedb.com/software_subscriptions/add/products/tpa/)
through the 2ndQuadrant Portal.

Then run the following commands:

```bash
# Install packages (Debian, Ubuntu)
$ sudo apt-get install tpaexec

# Install packages (RedHat)
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

[Subscribe to the "products/tpa/release" repository](https://techsupport.enterprisedb.com/software_subscriptions/add/products/tpa/)
to install the latest TPAexec packages.
(Login to the 2ndQuadrant Portal, add a subscription under
Support/Software/Subscriptions, and follow the instructions to enable
the repository on your system.)

```bash
# Debian or Ubuntu
$ sudo apt-get install tpaexec

# RedHat, Rocky or AlmaLinux
$ sudo yum install tpaexec
```

This will install TPAexec into `/opt/EDB/TPA`. It will also
ensure that other required packages (e.g., Python 3.6 or later) are
installed.

We mention `sudo` here only to indicate which commands need root
privileges. You may use any other means to run the commands as root.

## Python environment

Next, run `tpaexec setup` to create an isolated Python environment and
install the correct versions of all required modules.

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
export PATH=$PATH:/opt/EDB/TPA/bin
```

### Installing without network access

When you run `tpaexec setup`, it will ordinarily download the Python
packages from the network. The `tpaexec-deps` package (available from
the same repository as tpaexec) bundles everything that would have been
downloaded, so that they can be installed without network access. Just
install the package before you run `tpaexec setup` and the bundled
copies will be used automatically.

## Verification

Once you're done with all of the above steps, run the following command
to verify your local installation:

```bash
$ tpaexec selftest
```

If that command completes without any errors, your TPAexec installation
is ready for use.

## Upgrading

To upgrade to a later release of TPAexec, you must:

1. Install the latest `tpaexec` package
2. Install the latest `tpaexec-deps` package (if required; see above)
3. Run `tpaexec setup` again

If you have subscribed to the TPAexec package repository as described
above, running `apt-get update && apt-get upgrade` or `yum update`
should install the latest available versions of these packages. If not,
you can install the packages by any means available.

We recommend that you run `tpaexec setup` again whenever a new version
of `tpaexec` is installed. Some new releases may not strictly require
this, but others will not work without it.
