---
description: Which Linux distributions are supported by TPA.
---

# Distribution support

TPA detects and adapts to the distribution running on each target
instance. This page lists platforms which are actively supported and
'legacy distributions' which have previously been supported. Deploying
to a legacy platform is likely to work as long as you have access to the
necessary packages, but this is not considered a supported use of TPA
and is not suitable for production use.

Fully supported platforms are supported both as host systems for running
TPA and target systems on which TPA deploys the Postgres cluster.

Platforms marked 'experimentally supported' are recent releases that TPA
recognises and can deploy to, but for which not every architecture or
software option works yet, because that depends on packages having been
published for the platform upstream. They are not suitable for production
use until they become fully supported.

## ARM64 (aarch64) distros

### Debian

* Debian 13/trixie is experimentally supported
* Debian 12/bookworm is fully supported

### RedHat

* RHEL/Rocky/AlmaLinux/Oracle Linux 10.x is fully supported 
  (python3 only)
* RHEL/Rocky/AlmaLinux/Oracle Linux 9.x is fully supported 
  (python3 only)

## x86 (amd64) distros

### Debian

* Debian 13/trixie is experimentally supported
* Debian 12/bookworm is fully supported
* Debian 11/bullseye is fully supported
* Debian 10/buster is a legacy distribution
* Debian 9/stretch is a legacy distribution
* Debian 8/jessie is a legacy distribution

### Ubuntu

* Ubuntu 24.04/noble is fully supported
* Ubuntu 22.04/jammy is fully supported
* Ubuntu 20.04/focal is a legacy distribution
* Ubuntu 18.04/bionic is a legacy distribution
* Ubuntu 16.04/xenial is a legacy distribution

### RedHat

* RHEL/Rocky/AlmaLinux/Oracle Linux 10.x is fully supported 
  (python3 only)
* RHEL/Rocky/AlmaLinux/Oracle Linux 9.x is fully supported 
  (python3 only)
* RHEL/CentOS/Rocky/AlmaLinux/Oracle Linux 8.x is fully supported 
  (python3 only)
* RHEL/CentOS 7.x is a legacy distribution (python2 only)

!!! Warning
To deploy to instances running RHEL 8.x or equivalents, the TPA
controller must also be running RHEL 8.x . This is because a TPA
controller running another OS may be running a newer ansible version
than ansible-core 2.16, and therefore be incompatible with RHEL 8.x
on the target instances.
!!!

### SLES

* SLES 15 SP7 is fully supported

!!! Note 
M1 architecture using Repmgr in combination with EDBPGE or EPAS
is not supported for SLES. Use community PostgreSQL in this situation.
!!!

## IBM Power (ppc64le) distros

### RedHat

* RHEL/Rocky/AlmaLinux 10.x is fully supported (python3 only)
* RHEL/Rocky/AlmaLinux 9.x is fully supported (python3 only)
* RHEL/AlmaLinux 8.x is fully supported (python3 only)

## IBM Linux One (s390x) distros

### RedHat

* RHEL 10.x is fully supported (python3 only)
* RHEL 9.x is fully supported (python3 only)
* RHEL 8.x is fully supported (python3 only)

### SLES

* SLES 15 SP7 is fully supported

!!! Note 
M1 architecture using Repmgr in combination with EDBPGE or EPAS
is not supported for SLES. Use community PostgreSQL in this situation.
!!!

## Platform-specific considerations

When using the Docker platform, TPA will use the native architecture of
the host for the containers. For example, containers created on an x86
machine will use the x86 architecture.

When using the [AWS platform](platform-aws.md), TPA creates x86 virtual
machines by default. You can switch to ARM by selecting an ARM instance
type and AMI.

Legacy distributions may not be available in Docker or AWS depending on
whether images are available and maintained. For example, Debian 8 and
Ubuntu 16.04 are not available in [Docker
containers](platform-docker.md).
