2ndQuadrant TPA
===============

Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

Confidential property of 2ndQuadrant; not for public release.

## Overview

TPA (Trusted Postgres Architecture) is a set of recommendations from
2ndQuadrant about how to set up a Postgres cluster in various scenarios.
These represent the best practices followed by 2ndQuadrant, and are as
applicable to quick testbed setups as to production environments.

TPAexec is an orchestration tool that uses Ansible to build Postgres
clusters according to 2ndQuadrant's recommendations.

## What can TPAexec do?

With TPAexec, you can:

1. Provision hosts and other resources on AWS and other platforms,
   including existing (already-provisioned or bare metal) servers.

2. Configure the operating system (tweak kernel settings, install
   packages, create users, set up password-less ssh between hosts…)

3. Deploy Postgres, BDR, pglogical, Postgres extensions (from source or
   packages), repmgr and Barman, etc.

4. Run automated tests on the cluster after deployment

TPAexec will generate an initial configuration for the type of cluster
you want. You can use this default configuration straightaway, or edit
it to suit your needs. In most cases, this simple text configuration
file is all you will need to set up your cluster.

If you ever need to extend the functionality of TPAexec, the full range
of Ansible functionality is at your disposal.

## How do I use it?

[Select an architecture](architectures/README.md) for your cluster,
e.g., M1 (a Postgres cluster with a single primary and multiple
replicas), and do something like this:

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
[installation instructions](docs/INSTALL.md) and
[documentation](docs/index.md).

Write to tpa@2ndQuadrant.com for help.
