TPAexec
=======

© Copyright 2ndQuadrant

Confidential property of 2ndQuadrant; not for public release.

## Overview

TPA (Trusted Postgres Architecture) is a set of recommendations from
2ndQuadrant about how to set up a Postgres cluster in various scenarios.
These represent the best practices followed by 2ndQuadrant, and are as
applicable to quick testbed setups as to production environments.

TPAexec is an orchestration tool that uses Ansible to build Postgres
clusters according to 2ndQuadrant's recommendations.

## What can TPAexec do?

TPAexec operates in four distinct stages:

1. Configuration
2. Provisioning
3. Deployment
4. Testing

### Configuration

The ``tpaexec configure`` command with a few command-line options will
generate a simple YAML configuration file to describe the cluster you
want. It is ready for immediate use, and you can modify it to better
suit your needs.

### Provisioning

The ``tpaexec provision`` command takes config.yml and creates instances
and other resources required by the cluster. The details of this process
depend on the selected platform.

For example, on AWS, given access with the necessary privileges, TPAexec
will provision EC2 instances and VPCs, subnets, routing tables, internet
gateways, security groups, EBS volumes, elastic IPs, and so on.

You can also "provision" existing servers by using the "bare" platform.
In this case, you provide ``tpaexec provision`` with details about your
existing servers (which may be bare metal servers, or those provisioned
earlier on some cloud platform), and they will be used in later stages
just as if they had been created by TPAexec.

You are not restricted to a single platform—you can spread your cluster
out across some AWS instances (in multiple regions) and some on-premise
servers, or servers in other data centres, as needed.

At the end of the provisioning stage, we have the required number of
instances with the basic operating system installed, and which we can
access via ssh (with sudo to root).

### Deployment

The ``tpaexec deploy`` command takes the details of the provisioned
servers (which may or may not have actually been created by ``tpaexec
provision``; but it doesn't matter where they came from as long as we
have ssh+sudo access to them) and installs Postgres and other software
and sets them up in the requested configuration. This includes setting
up replication, backups, and so on.

At the end of the deployment stage, you will have a cluster with
Postgres and other software running on it.

### Testing

The ``tpaexec test`` command executes various tests against the deployed
cluster to ensure that it is working as expected.

At the end of this stage, you will have a fully-functioning cluster.

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

## Installation

[TPAexec installation instructions](INSTALL.md)

## Clusters

[Cluster design and implementation considerations](TPAexec-Cluster_Design_and_Implementation_Considerations.md)

### Platforms
XXX

### Architectures
XXX

### Configuration

[tpaexec configure](TPAexec-Generate-configuration.md)

[Customising the cluster configuration](TPAexec-Postgres_configuration_and_other_customisations.md)

### Provisioning

[Provisioning a cluster](TPAexec-Provision.md)
(see also [provisioning on bare-metal servers](TPAexec-Provision-baremetal.md))

### Deployment

[Deploying software to a cluster](TPAexec-Deploy.md)
[Rehydrating a cluster](TPAexec-Rehydrate.md)

## Miscellaneous

[PuTTY configuration instructions](TPAexec-PuTTY_Config.md)

## Help

Write to tpa@2ndQuadrant.com for help.
