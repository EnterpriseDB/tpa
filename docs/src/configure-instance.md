---
description: Customising the deployment process on cluster instances.
---

# Instance configuration

This page presents an overview of the various controls that TPA
offers to customise the deployment process on cluster instances, with
links to more detailed documentation.

Before you dive into the details of deployment, it may be helpful to
read [an overview of configuring a cluster](configure-cluster.md) to
understand how cluster and instance variables and the other mechanisms
in config.yml work together to allow you to write a concise,
easy-to-review configuration.

## System-level configuration

The first thing TPA does is to ensure that Python is bootstrapped
and ready to execute Ansible modules (a distribution-specific process).
Then it completes various system-level configuration tasks before moving
on to [Postgres configuration](#postgres) below.

* [Distribution support](distributions.md)
* [Python environment](python.md) (`preferred_python_version`)
* [Environment variables](target_environment.md) (e.g., `https_proxy`)

### Package repositories

You can use the
[pre-deploy hook](tpaexec-hooks.md#pre-deploy)
to execute tasks before any package repositories are configured.

* [Configure YUM repositories](yum_repositories.md)
  (for RHEL, Rocky and AlmaLinux)

* [Configure APT repositories](apt_repositories.md)
  (for Debian and Ubuntu)

* [Configure EDB repositories](edb_repositories.md)
  (on any system)

* [Configure a local package repository](local-repo.md)
  (to ship packages to target instances)

You can use the
[post-repo hook](tpaexec-hooks.md#post-repo)
to execute tasks after package repositories have been configured (e.g.,
to correct a problem with the repository configuration before installing
any packages).

### Package installation

Once the repositories are configured, packages are installed at various
stages throughout the deployment, beginning with a batch of system
packages:

* [Install non-Postgres packages](packages.md)
  (e.g., acl, openssl, sysstat)

Postgres and other components (e.g., Barman, repmgr, pgbouncer) will be
installed separately according to the cluster configuration; these are
documented in their own sections below.

### Other system-level tasks

* [Create and mount filesystems](volumes.md) (including RAID,
  LUKS setup)
* [Upload artifacts](artifacts.md) (files, directories,
  tar archives)
* [Set sysctl values](sysctl_values.md)
* [Configure /etc/hosts](hosts.md)
* [Manage ssh_known_hosts entries](manage_ssh_hostkeys.md)
* [Add system locale](locale.md)

### Skipping deployment completely

To prevent TPA from doing any part of the deployment process on an
instance - in other words, if you want TPA to provision the instance and
then leave it alone - set the `provision_only` setting for the instance
to `true` in `config.yml`. This setting will make TPA omit the instance
entirely from the inventory which `tpaexec deploy` sees.
<!-- WIP

* [Configure OpenVPN](openvpn.md)
* [Configure syslog](syslog.md)

-->

## Postgres

Postgres configuration is an extended process that goes hand-in-hand
with setting up other components like repmgr and pgbouncer. It begins
with installing Postgres itself.

### Version selection

Use the [configure options](tpaexec-configure.md#software-versions) to
select a Postgres flavour and version, or set `postgres_version` in
config.yml to specify which Postgres major version you want to install.

That's all you really need to do to set up a working cluster. Everything
else on this page is optional. You can control every aspect of the
deployment if you want to, but the defaults are carefully tuned to give
you a sensible cluster as a starting point.

### Installation

The default `postgres_installation_method` is to install packages for
the version of Postgres you selected, along with various extensions,
according to the architecture's needs:

* [Install Postgres and Postgres-related packages](postgres_installation_method_pkg.md)
  (e.g., pglogical, BDR, etc.)

* [Build and install Postgres and extensions from source](postgres_installation_method_src.md)
  (for development and testing)

Whichever installation method you choose, TPA can give you the same
cluster configuration with a minimum of effort.

### Configuration

* [Configure the postgres Unix user](postgres_user.md)

* [Run initdb to create the PGDATA directory](initdb.md)

* [Configure pg_hba.conf](pg_hba.conf.md)
* [Configure pg_ident.conf](pg_ident.conf.md)
* [Configure postgresql.conf](postgresql.conf.md)

You can use the
[postgres-config hook](tpaexec-hooks.md#postgres-config)
to execute tasks after the Postgres configuration files have been
installed (e.g., to install additional configuration files).

Once the Postgres configuration is in place, TPA will go on to
install and configure other components such as Barman, repmgr,
pgbouncer, and haproxy, according to the details of the architecture.

## Other components

<!-- WIP

## repmgr

-->

* [Configure Barman](barman.md)
* [Configure pgbouncer](pgbouncer.md)
* [Configure haproxy](haproxy.md)
* [Configure HARP](harp.md)
* [Configure EFM](efm.md)

### Configuring and starting services

TPA will now install systemd service unit files for each service.
The service for Postgres is named `postgres.service`, and can be started
or stopped with `systemctl start postgres`.

In the first deployment, the Postgres service will now be started. If
you are running `tpaexec deploy` again, the service may be reloaded or
restarted depending on what configuration changes you may have made. Of
course, if the service is already running and there are no changes, then
it's left alone.

In any case, Postgres will be running at the end of this step.

## After starting Postgres

* [Create Postgres users](postgres_users.md)

* [Create Postgres tablespaces](postgres_tablespaces.md)

* [Create Postgres databases](postgres_databases.md)

* [Configure pglogical replication](pglogical.md)

* [Configure .pgpass](pgpass.md)

You can use the
[postgres-config-final hook](tpaexec-hooks.md#postgres-config-final)
to execute tasks after the post-startup Postgres configuration has been
completed (e.g., to perform SQL queries to create objects or load data).

* [Configure BDR](bdr.md)

You can use the
[post-deploy hook](tpaexec-hooks.md#post-deploy)
to execute tasks after the deployment process has completed.
