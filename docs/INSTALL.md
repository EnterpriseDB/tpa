# TPAexec installation

To use TPAexec, you need to install the tpaexec package and run the
``tpaexec setup`` command.

TPAexec packages are available to 2ndQuadrant customers by prior
arrangement.

## Quickstart

First, subscribe to the products/tpa/release repository through the
2ndQuadrant Portal software subscription mechanism. Then run the
following commands:

```bash
# Pick the command for your platform
[root]# apt-get install tpaexec
[root]# yum install tpaexec

# Post-installation setup
[root]# /opt/2ndQuadrant/TPA/bin/tpaexec setup

# Verify the installation
[tpa]$ /opt/2ndQuadrant/TPA/bin/tpaexec selftest
```

More detailed explanations below.

Commands run as root will be shown starting with a **[root]#**; commands
shown starting with a **[tpa]$** may be run by an ordinary user.

## What time is it?

Please make absolutely sure that your system has the correct date and
time set, because various things will fail otherwise. For example:

```bash
[root]# ntpdate pool.ntp.org
```

## Packages

Subscribe to the "products/tpa/release" repository to get the latest
TPAexec packages. Login to the 2ndQuadrant Portal, add a subscription
under Support/Software subscriptions, and follow the instructions to
enable the repository on your system.

Once that is done, you can install the tpaexec package as follows:

```bash
# Debian or Ubuntu
[root]# apt-get install tpaexec

# RedHat or CentOS
[root]# yum install tpaexec
```

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

```bash
# Create a virtualenv and install the pip modules (including ansible).
[root]# /opt/2ndQuadrant/TPA/bin/tpaexec setup
```

Now, as a non-root user, add the following to your .bashrc or
.profile (or equivalent shell startup configuration):

```bash
[tpa]$ export PATH=$PATH:/opt/2ndQuadrant/TPA/bin
```

### Installing without network access

When you run ``tpaexec setup``, it will ordinarily download the Python
packages from the network. The ``tpaexec-deps`` package (available from
the same repository as tpaexec) bundles everything that would have been
downloaded, so that they can be installed without network access. Just
install the package before you run ``tpaexec setup`` and the bundled
copies will be used automatically.

## Verification

Once you're done with all of the above steps, run the following command
to verify your local installation:

```bash
[tpa]$ tpaexec selftest
```

If that command completes without any errors, your TPAexec installation
is ready for use.
