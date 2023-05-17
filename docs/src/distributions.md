# Distribution support

TPA detects and adapts to the distribution running on each target
instance. This page lists platforms which are actively supported and
'legacy distribution' which have previously been supported. Deploying to a
legacy platform is likely to work as long as you have access to the
necessary packages, but this is not considered a supported use of TPA
and is not suitable for production use.

!!! Note
    This page is about distribution support on target instances that you
    are deploying *to*, not about the system you are running TPA *from*.
    See the [installation instructions](INSTALL.md#distribution-support) for
    more on the latter.
!!!

## Debian x86

* Debian 11/bullseye is fully supported
* Debian 10/buster is fully supported
* Debian 9/stretch is a legacy distribution
* Debian 8/jessie is a legacy distribution

## Ubuntu x86

* Ubuntu 22.04/jammy is fully supported
* Ubuntu 20.04/focal is fully supported
* Ubuntu 18.04/bionic is a legacy distribution
* Ubuntu 16.04/xenial is a legacy distribution

## RedHat x86

* RHEL/CentOS/Rocky/AlmaLinux 8.x is fully supported (python3 only)
* RHEL/CentOS 7.x is fully supported (python2 only)

## Platform-specific considerations

Some platforms may not work with the legacy distributions mentioned here.
For example, Debian 8 and Ubuntu 16.04 are not available in [Docker
containers](platform-docker.md).
