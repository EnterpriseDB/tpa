# TPA hooks

TPA can set up fully-functional clusters with no user intervention,
and already provides a broad variety of
[settings to control your cluster configuration](configure-instance.md),
including custom repositories and packages, custom Postgres
configuration (both pg_hba.conf and postgresql.conf), and so on.

You can write hook scripts to address specific needs that are not met by
the available configuration settings. Hooks allow you to execute
arbitrary Ansible tasks during the deployment.

Hooks are the ultimate extension mechanism for TPA, and there is no
limit to what you can do with them. Please use them with caution, and
keep in mind the additional maintenance burden you are taking on. The
TPA developers have no insight into your hook code, and cannot
guarantee compatibility between releases beyond invoking hooks at the
expected stage.

## Summary

If you create files with specific names under the `hooks` subdirectory
of your cluster directory, TPA will invoke them at various stages of
the deployment process, as described below.

```bash
$ mkdir ~/clusters/speedy/hooks
$ cat > ~/clusters/speedy/hooks/pre-deploy.yml
---
- debug: msg="hello world!"
```

Hook scripts are invoked with `include_tasks`, so they are expected to
be YAML files containing a list of Ansible tasks (not a playbook, which
contains a list of plays). Unless otherwise documented below, hooks are
unconditionally executed for all hosts in the deployment.

## General-purpose hooks

### pre-deploy

TPA invokes `hooks/pre-deploy.yml` immediately after bootstrapping
Python—but before doing anything else like configuring repositories and
installing packages. This is the earliest stage at which you can execute
your own code.

You can use this hook to set up custom repository configuration, beyond
what you can do with
[`apt_repositories`](apt_repositories.md) or
[`yum_repositories`](yum_repositories.md).

### post-repo

TPA invokes `hooks/post-repo.yml` after configuring package
repositories. You can use it to make corrections to the repository
configuration before beginning to install packages.

### pre-initdb

TPA invokes `hooks/pre-initdb.yml` before deciding whether or not to
[run initdb to create PGDATA](initdb.md) if it does not exist. You
should not ordinarily need to use this hook (but if you use it to create
`PGDATA` yourself, then TPA will skip `initdb`).

### postgres-config

TPA invokes `hooks/postgres-config.yml` after generating Postgres
configuration files, including pg_hba.conf and the files in conf.d, but
before the server has been started.

You can use this hook, for example, to create additional configuration
files under `conf.d`.

### postgres-config-final

TPA invokes `hooks/postgres-config-final.yml` after starting
Postgres and creating users, databases, and extensions. You can use this
hook to execute SQL commands, for example, to perform custom extension
configuration or create database objects.

### harp-config

TPA invokes `hooks/harp-config.yml` after generating HARP configuration
files, but before the HARP service has been started.

You can use this hook, for example, to perform any customizations to the HARP
proxy that are not provided by the built-in interface of TPA.

Please note that this hook will be run in any node that installs HARP packages,
including PGD nodes.

### post-deploy

TPA invokes `hooks/post-deploy.yml` at the end of the deployment.

You can go on to do whatever you want after this stage.

If you use this hook to make changes to any configuration files that
were generated or altered during the TPA deployment, you run the
risk that the next `tpaexec deploy` will overwrite your changes (since
TPA doesn't know what your hook might have done).

## PGD hooks

These hooks are specific to PGD deployments.

### bdr-pre-node-creation

TPA invokes `hooks/bdr-pre-node-creation.yml` on all instances
before creating a PGD node on any instance for the first time. The hook
will not be invoked if all required PGD nodes already exist.

### bdr-post-group-creation

TPA invokes `hooks/bdr-post-group-creation.yml` on all instances
after creating any PGD node group on the `first_bdr_primary` instance.
The hook will not be invoked if the required PGD groups already exist.

### bdr-pre-group-join

TPA invokes `hooks/bdr-pre-group-join.yml` on all instances
after creating, changing or removing the replication sets and
configuring the required subscriptions, before the node join.

You can use this hook to execute SQL commands and perform other
adjustments to the replication set configuration and subscriptions that
might be required before the node join starts.

For example, you can adjust the PGD witness replication set to
automatically add new tables and create DDL filters in general.

## Other hooks

### postgres-pre-update, postgres-post-update

The [`upgrade`](tpaexec-upgrade.md) command invokes
`hooks/postgres-pre-update.yml` on a particular instance before it
installs any packages, and invokes `hooks/postgres-post-update.yml`
after the package installation is complete. Both hooks are invoked only
on the instance being updated.

You can use these hooks to customise the update process for your
environment (e.g., to install other packages and stop and restart
services that TPA does not manage).

## New hooks

EDB adds new hooks to TPA as the need arises. If your use case is not
covered by the existing hooks, please contact us to discuss the matter.
