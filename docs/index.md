TPAexec
=======

© Copyright 2ndQuadrant

Confidential property of 2ndQuadrant; not for public release.

## Introduction

TPA (Trusted Postgres Architecture) is a set of recommendations from
2ndQuadrant about how to set up a Postgres cluster in various scenarios.
These represent the best practices followed by 2ndQuadrant, and are as
applicable to quick testbed setups as to production environments.

TPAexec is an orchestration tool that uses Ansible to build Postgres
clusters according to 2ndQuadrant's recommendations.

### Architectures

An architecture is a recommended layout of servers and software to set
up Postgres for a specific purpose.

Examples include "M1" (Postgres with a primary and multiple streaming
replicas) and "BDR-Always-ON" (Postgres with BDR in a configuration
meant for HA).

### Platforms

A platform is a means to host the servers to deploy any architecture.
Examples include AWS, lxd, and bare-metal servers.

## What can TPAexec do?

TPAexec operates in four distinct stages to bring up a Postgres cluster:

```bash
# 1. Configuration—decide what kind of cluster you want
[tpa]$ tpaexec configure clustername --architecture M1

# 2. Provisioning—create the servers needed to host the cluster
[tpa]$ tpaexec provision clustername

# 3. Deployment—install and configure the necessary software
[tpa]$ tpaexec deploy clustername

# 4. Testing—make sure everything is working as expected
[tpa]$ tpaexec test clustername
```

TPAexec itself can operate from your laptop, an EC2 instance, or any
machine that can reach the cluster's servers over the network.

### Configuration

The [``tpaexec configure``](tpaexec-configure.md)
command generates a simple YAML configuration file to describe the
cluster you want. The configuration is ready for immediate use, and you
can modify it to better suit your needs. Editing the configuration file
is the usual way to make any configuration changes to your cluster,
both before and after it's created.

### Provisioning

The [``tpaexec provision``](tpaexec-provision.md)
command creates instances and other resources required by the cluster.
The details of the process depend on the architecture (e.g., M1) and
platform (e.g., AWS) that you selected while configuring the cluster.

For example, given AWS access with the necessary privileges, TPAexec
will provision EC2 instances, VPCs, subnets, routing tables, internet
gateways, security groups, EBS volumes, elastic IPs, etc.

You can also "provision" existing servers by selecting the "bare"
platform and providing connection details. Whether these are bare metal
servers or those provisioned separately on a cloud platform, they can be
used just as if they had been created by TPAexec.

You are not restricted to a single platform—you can spread your cluster
out across some AWS instances (in multiple regions) and some on-premise
servers, or servers in other data centres, as needed.

At the end of the provisioning stage, you will have the required number
of instances with the basic operating system installed, which TPAexec
can access via ssh (with sudo to root).

### Deployment

The [``tpaexec deploy``](tpaexec-deploy.md)
command installs and configures Postgres and other software on the
provisioned servers (which may or may not have been created by TPAexec;
but it doesn't matter who created them so long as ssh and sudo access is
available). This includes setting up replication, backups, and so on.

At the end of the deployment stage, Postgres will be up and running.

### Testing

The [``tpaexec test``](tpaexec-test.md) command executes various
architecture and platform-specific tests against the deployed cluster to
ensure that it is working as expected.

At the end of the testing stage, you will have a fully-functioning
cluster.

### Incremental changes

TPAexec is carefully designed so that the provisioning, deployment, and
testing stages are idempotent. You can run through them, make a change
to config.yml, and run through the process again to deploy the change.
If nothing has changed in the configuration or on the instances, then
rerunning the entire process will not change anything either.

### Extensible through Ansible

In most cases, you can make the necessary changes to your cluster by
editing the config.yml file and running the provision/deploy/test cycle.
Should you need to go beyond what is already implemented in TPAexec, the
full range of Ansible functionality is at your disposal at every stage.

### Cluster management

Once your cluster is up and running, TPAexec provides convenient cluster
management functions, including configuration changes, switchover, and
zero-downtime minor-version upgrades. These features make it easier and
safer to manage your cluster than making the changes by hand.

## It's just Postgres

TPAexec can create complex clusters with many features configured, but
the result is just Postgres. The installation follows some conventions
designed to make life simpler, but there is no hidden magic or anything
standing in the way between you and the database. You can do everything
on a TPA cluster that you could do on any other Postgres installation.
