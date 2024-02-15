# Distribution support

TPA detects and adapts to the distribution running on each target
instance. Listed here are the platforms that are actively supported and
legacy distributions that were previously supported. 

Deploying to a legacy platform is likely to work as long as you have access to the
necessary packages. However, this isn't a supported use of TPA
and isn't suitable for production use.

Fully supported platforms are supported both as host systems for running
TPA and target systems on which TPA deploys the Postgres cluster.

## Debian x86

* Debian 11/bullseye is fully supported.
* Debian 10/buster is fully supported.
* Debian 9/stretch is a legacy distribution.
* Debian 8/jessie is a legacy distribution.

## Ubuntu x86

* Ubuntu 22.04/jammy is fully supported.
* Ubuntu 20.04/focal is fully supported.
* Ubuntu 18.04/bionic is a legacy distribution.
* Ubuntu 16.04/xenial is a legacy distribution.

## Oracle Linux

* Oracle Linux 9.x is fully supported (Docker only).
* Oracle Linux 8.x is fully supported (Docker only).
* Oracle Linux 7.x is fully supported (Docker only).

## RedHat x86

* RHEL/Rocky/AlmaLinux/Oracle Linux 9.x is fully supported (Python 3 only).
* RHEL/CentOS/Rocky/AlmaLinux 8.x is fully supported (Python 3 only).
* RHEL/CentOS 7.x is fully supported (Python 2 only).

## SLES

* SLES 15.x is fully supported.

## Platform-specific considerations

Some platforms might not work with the legacy distributions mentioned here.
For example, Debian 8 and Ubuntu 16.04 aren't available in [Docker
containers](platform-docker.md).
