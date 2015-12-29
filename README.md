2ndQuadrant CustomCloud
=======================

© Copyright 2ndQuadrant, 2013

Confidential property of 2ndQuadrant; not for public release.

This repository contains automation tools to provision, configure, and
operate Postgres database clusters. They represent the best practices
followed by 2ndQuadrant to set up Postgres, and are equally applicable
to setting up quick one-off testbeds or production environments for
customers.

With CustomCloud, you can:

1. Provision hosts and other resources on AWS (and, in future, other
   platforms)

2. Configure the operating system (tweak kernel settings, install
   packages, create users, set up password-less ssh between hosts…)

3. Deploy Postgres or Postgres-XL (from source or packages), Postgres
   extensions, repmgr and Barman, etc.

In most cases, a few simple configuration files are all you will need,
but you can easily customise the process to handle more complex setup
tasks and configurations.

I don't care, I just want a test cluster
========================================

1. You need 2ndQuadrant's fork of Ansible.
   [Read the INSTALL guide](INSTALL.md) for details.

2. You need an AWS access key id and secret access key for API access.
   [Read platforms/aws/README](platforms/aws/README) for details.

3. Pick a name for the cluster, and write a clustername/config.yml file
   describing the required instances, and a clustername/deploy.yml file
   to apply the desired roles to these instances.
   [Read clusters/README](clusters/README) for details.
    
4. Provision the cluster instances and deploy software to them:

   ```
   utils/ansible-playbook platforms/aws/provision.yml \
       -e cluster=./clusters/name

   utils/ansible-playbook -i inventory/ec2.py clusters/name/deploy.yml \
       -e cluster=./clusters/name
   ```

5. Once you're done with testing, deprovision the cluster:

   ```
   utils/ansible-playbook -i inventory/ec2.py platforms/aws/deprovision.yml \
       -e cluster=./clusters/name
   ```

Note that deprovision.yml does not currently remove additional volumes
that are provisioned with delete_on_termination disabled. Such volumes
**MUST BE DELETED** by hand for now.

--
Abhijit Menon-Sen <ams@2ndQuadrant.com>
