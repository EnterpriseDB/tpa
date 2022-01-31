# Distribution support

TPAexec detects and adapts to the distribution running on each target
instance.

(This page is about distribution support on target instances that you
are deploying *to*, not about the system you are running TPAexec *from*.
See the [installation instructions](INSTALL.md#distribution-support) for
more on the latter.)

## Debian

* Debian 10/buster is fully supported
* Debian 9/stretch is supported as a legacy platform
* Debian 8/jessie is supported as a legacy platform

## Ubuntu

* Ubuntu 20.04/focal is fully supported
* Ubuntu 18.04/bionic is fully supported
* Ubuntu 16.04/xenial is supported as a legacy platform

## RedHat

* RHEL/CentOS/Rocky/AlmaLinux 8.x is fully supported (python3 only)
* RHEL/CentOS 7.x is fully supported (python2 only)

## Package availability

All combinations of packages for Postgres and other components may not
be available for all of the supported distributions. For example, you
will need to use an older distribution to be able to install Postgres
9.4 with BDRv1 from packages; and not all projects publish Ubuntu 20.04
packages yet.

## Platform-specific considerations

Some platforms may not support all of the distributions mentioned here.
For example, Debian 8 and Ubuntu 16.04 are not supported in [Docker
containers](platform-docker.md).
