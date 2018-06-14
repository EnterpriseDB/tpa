2ndQuadrant TPA
===============

© Copyright 2ndQuadrant, 2014-2018

Confidential property of 2ndQuadrant; not for public release.

This repository contains automation tools to provision, configure, and
operate Postgres database clusters. They represent the best practices
followed by 2ndQuadrant to set up Postgres, and are equally applicable
to setting up quick one-off testbeds or production environments for
customers.

With TPA, you can:

1. Provision hosts and other resources on AWS (and, in future, other
   platforms)

2. Configure the operating system (tweak kernel settings, install
   packages, create users, set up password-less ssh between hosts…)

3. Deploy Postgres, Postgres-BDR, or Postgres-XL (from source or
   packages), Postgres extensions, repmgr and Barman, etc.

In most cases, a few simple configuration files are all you will need,
but you can easily customise the process to handle more complex setup
tasks and configurations.

Pre-requisites
==============

1. You need Python, Ansible, and various Python modules.
   [Read the INSTALL guide](INSTALL.md) for details.

2. You need an AWS access key id and secret access key for API access.
   [Read platforms/aws/README](platforms/aws/README.md) for details.

3. You may need to set the repo password for the relevant 2ndQuadrant repo [rpm-internal.2ndquadrant.com](https://rpm-internal.2ndquadrant.com/site/content/) or [apt-internal.2ndquadrant.com](https://apt-internal.2ndquadrant.com/site/content/)
   ```
   export TPA_2Q_REPO_PASSWORD=putPASSWORDhere
   ```

I just want a test cluster
==========================

1. Pick a name for the cluster, and write a clustername/config.yml file
   describing the required instances, and a clustername/deploy.yml file
   to apply the desired roles to these instances.
   [Read clusters/README](clusters/README.md) for details.
    
2. Provision the cluster instances and deploy software to them:

   ```
   tpaexec provision path-to-clusterdir

   tpaexec deploy path-to-clusterdir
   ```

3. Once you're done with testing, deprovision the cluster:

   ```
   tpaexec deprovision path-to-clusterdir
   ```

Help
====

Write to tpa@2ndQuadrant.com for help.
