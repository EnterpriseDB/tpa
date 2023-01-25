EDB TPA
=======

© Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

Confidential property of EDB; not for public release.

## Overview

TPA is an orchestration tool that uses Ansible to build Postgres
clusters according to EDB's recommendations.

These recommendations represent the best practices followed by EDB, and
comprise many years of hard-earned experience of deploying Postgres and
associated components in various scenarios.

## What can TPA do?

With TPA, you can:

1. Provision hosts and other resources on AWS and other platforms,
   including existing (already-provisioned or bare metal) servers.

2. Configure the operating system (tweak kernel settings, install
   packages, create users, set up password-less ssh between hosts…)

3. Deploy Postgres, BDR, pglogical, Postgres extensions (from source or
   packages), repmgr and Barman, etc.

4. Run automated tests on the cluster after deployment

TPA will generate an initial configuration for the type of cluster
you want. You can use this default configuration straightaway, or edit
it to suit your needs. In most cases, this simple text configuration
file is all you will need to set up your cluster.

If you ever need to extend the functionality of TPA, the full range
of Ansible functionality is at your disposal.

## Installation

To use TPA, you need to install tpaexec and run the `tpaexec setup`
command. Please use the [TPA packages](docs/src/INSTALL.md) if they are
available for your platform.

If you have an EDB Github account that gives you access to the TPA
repository, and you want to use TPA on MacOS X or another platform
for which packages are not available, you can [install it from
source](docs/src/INSTALL-repo.md) or [run it inside a Docker
container](docs/src/INSTALL-docker.md).

## How do I use it?

Select an architecture for your cluster,
e.g., [M1](docs/src/architecture-M1.md) (a Postgres cluster with a single
primary and multiple replicas), and do something like this:

```
# Generate an initial configuration for the cluster. This command
# accepts many options. See 'tpaexec info architectures/M1' and
# 'tpaexec help configure-options' for more details.
tpaexec configure clustername --architecture M1

# You can examine the generated clustername/config.yml here, and edit it
# if you want to, or just stick with the defaults.

# Now bring up the cluster
tpaexec provision clustername
tpaexec deploy clustername
tpaexec test clustername

# (Remember to destroy the cluster when you're done with it.)
tpaexec deprovision clustername
```

For more details, please consult the
[installation instructions](docs/src/INSTALL.md) and
[documentation](docs/src/index.md).

Write to tpa@enterprisedb.com for help.
