# Upgrading your cluster

The `tpaexec upgrade` command is used to upgrade the software running on
your TPA cluster (`tpaexec deploy` will not perform upgrades).

(This command replaces the earlier `tpaexec update-postgres` command.)

## Introduction

If you make any changes to config.yml, the way to apply those changes is
to run `tpaexec provision` followed by `tpaexec deploy`.

The exception to this rule is that `tpaexec deploy` will refuse to
install a different version of a package that is already installed.
Instead, you must use `tpaexec upgrade` to perform software upgrades.

This command will try to perform the upgrade with minimal disruption to
cluster operations. The exact details of the specialised upgrade process
depend on the architecture of the cluster, as documented below.

When upgrading, you should always use barman to take a backup before
beginning the upgrade and disable any scheduled backups which would take
place during the time set aside for the upgrade.

In general, TPA will proceed instance-by-instance, stopping any affected
services, installing new packages, updating the configuration if needed,
restarting services, and performing any runtime configuration changes,
before moving on to do the same thing on the next instance. At any time
during the process, only one of the cluster's nodes will be unavailable.

When upgrading a cluster to PGD-Always-ON or upgrading an existing
PGD-Always-ON cluster, you can enable monitoring of the status of your
proxy nodes during the upgrade by adding the option
`-e enable_proxy_monitoring=true` to your `tpaexec upgrade` command
line. If enabled, this will create an extra table in the bdr database
and write monitoring data to it while the upgrade takes place. The
performance impact of enabling monitoring is very small and it is
recommended that it is enabled.

## Configuration

In many cases, minor-version upgrades do not need changes to config.yml.
Just run `tpaexec upgrade`, and it will upgrade to the latest available
versions of the installed packages in a graceful way (what exactly that
means depends on the details of the cluster).

Sometimes an upgrade involves additional steps beyond installing new
packages and restarting services. For example, in order to upgrade from
BDR4 to PGD5, one must set up new package repositories and make certain
changes to the BDR node and group configuration during the process.

In such cases, where there are complex steps required as part of the
process of effecting a software upgrade, `tpaexec upgrade` will perform
those steps. For example, in the above scenario, it will configure the
new PGD5 package repositories (which deploy would also normally do).

However, it will make only those changes that are directly required by
the upgrade process itself. For example, if you edit config.yml to add a
new Postgres user or database, those changes will not be done during the
upgrade. To avoid confusion, we recommend that you `tpaexec deploy` any
unrelated pending changes before you begin the software upgrade process.

## Upgrading from BDR-Always-ON to PGD-Always-ON

**Note:** The upgrade procedure from BDR-Always-ON to PGD-Always-ON for
camo enabled clusters using BDR version 3.7 is not yet supported. This
support will come in a later release.

To upgrade from BDR-Always-ON to PGD-Always-ON (that is, from BDR3/4 to
PGD5), first run `tpaexec reconfigure`:

```
$ tpaexec reconfigure ~/clusters/speedy\
  --architecture PGD-Always-ON\
  --pgd-proxy-routing local
```

This command will read config.yml, work out the changes necessary to
upgrade the cluster, and write a new config.yml. For details of its
invocation, see [the command's own
documentation](tpaexec-reconfigure.md). After reviewing the
changes, run `tpaexec upgrade` to perform the upgrade:

```
$ tpaexec upgrade ~/clusters/speedy\
```

Or to run the upgrade with proxy monitoring enabled,

```
$ tpaexec upgrade ~/clusters/speedy\
  -e enable_proxy_monitoring=true
```

`tpaexec upgrade` will automatically run `tpaexec provision`, to update
the ansible inventory. The upgrade process does the following:

1. Checks that all preconditions for upgrading the cluster are met.
2. For each instance in the cluster, checks that it has the correct
   repositories configured and that the required postgres packages are
   available in them.
3. For each BDR node in the cluster, one at a time:
    - Fences the node off to ensure that harp-proxy doesn't send any
      connections to it.
    - Stops, updates, and restarts postgres, including replacing BDR4
      with PGD5.
    - Unfences the node so it can receive connections again.
    - Updates pgbouncer and pgd-cli, as applicable for this node.
4. For each instance in the cluster, updates its BDR configuration
   specifically for BDR v5
5. For each proxy node in the cluster, one at a time:
    - Sets up pgd-proxy.
    - Stops harp-proxy.
    - Starts pgd-proxy.
6. Removes harp-proxy and its support files.

## PGD-Always-ON

When upgrading an existing PGD-Always-ON (PGD5) cluster to the latest available
software versions, the upgrade process does the following:

1. Checks that all preconditions for upgrading the cluster are
   met.
2. For each instance in the cluster, checks that it has the correct
   repositories configured and that the required postgres packages are
   available in them.
3. For each BDR node in the cluster, one at a time:
    - Fences the node off to ensure that pgd-proxy doesn't send any
      connections to it.
    - Stops, updates, and restarts postgres.
    - Unfences the node so it can receive connections again.
    - Updates pgbouncer, pgd-proxy, and pgd-cli, as applicable for this
      node.

## BDR-Always-ON

For BDR-Always-ON clusters, the upgrade process goes through the cluster instances
one by one and does the following:

1. Tell haproxy the server is under maintenance.
2. If the instance was the active server, request pgbouncer to reconnect
   and wait for active sessions to be closed.
3. Stop Postgres, update packages, and restart Postgres.
5. Finally, mark the server as "ready" again to receive requests through
   haproxy.

PGD logical standby or physical replica instances are updated without
any haproxy or pgbouncer interaction. Non-Postgres instances in the
cluster are left alone.

You can control the order in which the cluster's instances are updated
by defining the `update_hosts` variable:

```
$ tpaexec upgrade ~/clusters/speedy \
  -e update_hosts=quirk,keeper,quaver
```

This may be useful to minimise lead/shadow switchovers during the update
by listing the active PGD primary instances last, so that the shadow
servers are updated first.

If your environment requires additional actions, the
[postgres-pre-update and postgres-post-update hooks](tpaexec-hooks.md)
allow you to execute custom Ansible tasks before and after the package
installation step.

## M1

For M1 clusters, `upgrade` will first update the streaming
replicas one by one, then perform a [switchover](tpaexec-switchover.md)
from the primary to one of the replicas, update the primary, and
switchover back to it again.

## Package version selection

By default, `tpaexec upgrade` will update to the latest
available versions of the installed packages if you did not explicitly
specify any package versions (e.g., Postgres, PGD, or pglogical) when
you created the cluster.

If you did select specific versions, for example by using any of the
`--xxx-package-version` options (e.g., postgres, bdr, pglogical) to
[`tpaexec configure`](tpaexec-configure.md), or by defining
`xxx_package_version` variables in config.yml, the upgrade will do
nothing because the installed packages already satisfy the requested
versions.

In this case, you must edit config.yml, remove the version settings, and
re-run `tpaexec provision`. The update will then install the latest
available packages. You can still update to a specific version by
specifying versions on the command line as shown below:

```
$ tpaexec upgrade ~/clusters/speedy -vv         \
  -e postgres_package_version="2:11.6r2ndq1.6.13*"      \
  -e pglogical_package_version="2:3.6.11*"              \
  -e bdr_package_version="2:3.6.11*"
```

Please note that version syntax here depends on your OS distribution and
package manager. In particular, yum accepts `*xyz*` wildcards, while
apt only understands `xyz*` (as in the example above).

Note: see limitations of using wildcards in package_version in
[tpaexec-configure](tpaexec-configure.md#known-issue-with-wildcard-use).

It is your responsibility to ensure that the combination of Postgres,
PGD, and pglogical package versions that you request are sensible. That
is, they should work together, and there should be an upgrade path from
what you have installed to the new versions.

For PGD clusters, it is a good idea to explicitly specify exact versions
for all three components (Postgres, PGD, pglogical) rather than rely on
the package manager's dependency resolution to select the correct
dependencies.

We strongly recommend testing the upgrade in a QA environment before
running it in production.
