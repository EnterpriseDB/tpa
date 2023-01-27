# TPA

© Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

Confidential property of EDB; not for public release.

[Link to TPA documentation in PDF format](tpaexec.pdf)

## Introduction

TPA is an orchestration tool that uses Ansible to build Postgres
clusters according to EDB's recommendations.

TPA embodies the best practices followed by EDB, and is informed by many
years of experience with deploying Postgres and associated components in
various scenarios. These recommendations are as applicable to quick
testbed setups as to production environments.

(You can skip straight to the [TPA installation
instructions](INSTALL.md) if you want to get started.)

## What can TPA do?

TPA operates in four distinct stages to bring up a Postgres cluster:

* Generate a cluster [configuration](#configuration)
* [Provision](#provisioning) servers (VMs, containers) to host the cluster
* [Deploy](#deployment) software to the provisioned instances
* [Test](#testing) the deployed cluster

```bash
# 1. Configuration: decide what kind of cluster you want
[tpa]$ tpaexec configure clustername --architecture M1 --platform aws

# 2. Provisioning: create the servers needed to host the cluster
[tpa]$ tpaexec provision clustername

# 3. Deployment: install and configure the necessary software
[tpa]$ tpaexec deploy clustername

# 4. Testing: make sure everything is working as expected
[tpa]$ tpaexec test clustername
```

You can run TPA from your laptop, an EC2 instance, or any machine
that can reach the cluster's servers over the network.

Here's a [list of capabilities and supported software](tpaexec-support.md).

### Configuration

The [`tpaexec configure`](tpaexec-configure.md)
command generates a simple YAML configuration file to describe a
cluster, based on the options you select. The configuration is ready for
immediate use, and you can modify it to better suit your needs. Editing
the configuration file is the usual way to [make any configuration
changes to your cluster](configure-cluster.md), both before and after
it's created.

At this stage, you must select an architecture and a platform for the
cluster. An **architecture** is a recommended layout of servers and
software to set up Postgres for a specific purpose. Examples include
"M1" (Postgres with a primary and streaming replicas) and
"BDR-Always-ON" (Postgres with BDR in an HA configuration). A
**platform** is a means to host the servers to deploy any architecture,
e.g., AWS, Docker, or bare-metal servers.

### Provisioning

The [`tpaexec provision`](tpaexec-provision.md)
command creates instances and other resources required by the cluster.
The details of the process depend on the architecture (e.g., M1) and
platform (e.g., AWS) that you selected while configuring the cluster.

For example, given AWS access with the necessary privileges, TPA
will provision EC2 instances, VPCs, subnets, routing tables, internet
gateways, security groups, EBS volumes, elastic IPs, etc.

You can also "provision" existing servers by selecting the "bare"
platform and providing connection details. Whether these are bare metal
servers or those provisioned separately on a cloud platform, they can be
used just as if they had been created by TPA.

You are not restricted to a single platform—you can spread your cluster
out across some AWS instances (in multiple regions) and some on-premise
servers, or servers in other data centres, as needed.

At the end of the provisioning stage, you will have the required number
of instances with the basic operating system installed, which TPA
can access via SSH (with sudo to root).

### Deployment

The [`tpaexec deploy`](tpaexec-deploy.md)
command installs and configures Postgres and other software on the
provisioned servers (which may or may not have been created by TPA;
but it doesn't matter who created them so long as SSH and sudo access is
available). This includes setting up replication, backups, and so on.

At the end of the deployment stage, Postgres will be up and running.

### Testing

The [`tpaexec test`](tpaexec-test.md) command executes various
architecture and platform-specific tests against the deployed cluster to
ensure that it is working as expected.

At the end of the testing stage, you will have a fully-functioning
cluster.

### Incremental changes

TPA is carefully designed so that provisioning, deployment, and
testing are idempotent. You can run through them, make a change to
config.yml, and run through the process again to deploy the change. If
nothing has changed in the configuration or on the instances, then
rerunning the entire process will not change anything either.

### Cluster management

Once your cluster is up and running, TPA provides convenient cluster
management functions, including configuration changes, switchover, and
zero-downtime minor-version upgrades. These features make it easier and
safer to manage your cluster than making the changes by hand.

### Extensible through Ansible

TPA supports a [variety of configuration
options](configure-instance.md), so you can do a lot just by editing
config.yml and re-running provision/deploy/test. If you do need to go
beyond what TPA already supports, you can write

* [Custom commands](tpaexec-commands.md), which make it simple to write
  playbooks to run on the cluster. Just create
  `commands/xyz.yml` in your cluster directory, and invoke it
  using `tpaexec xyz /path/to/cluster`. Ideal for any management tasks
  or processes that you need to automate.

* [Custom tests](tpaexec-tests.md), which augment the builtin tests with
  in-depth verifications specific to your environment and application.
  Using `tpaexec test` to run all tests in a uniform, repeatable way
  ensures that you will not miss out on anything important, either when
  dealing with a crisis, or just during routine cluster management.

* [Hook scripts](tpaexec-hooks.md), which are invoked during various
  stages of the deployment. For example, tasks in `hooks/pre-deploy.yml`
  will be run before the main deployment; there are many other hooks,
  including `post-deploy`. This places the full range of Ansible
  functionality at your disposal.

## It's just Postgres

TPA can create complex clusters with many features configured, but
the result is just Postgres. The installation follows some conventions
designed to make life simpler, but there is no hidden magic or anything
standing in the way between you and the database. You can do everything
on a TPA cluster that you could do on any other Postgres installation.

## Getting started

Follow the [TPA installation instructions](INSTALL.md) for your
system, then [configure your first cluster](tpaexec-configure.md).
