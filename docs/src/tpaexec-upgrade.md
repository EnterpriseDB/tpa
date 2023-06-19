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

In general, TPA will proceed instance-by-instance, stopping any affected
services, installing new packages, updating the configuration if needed,
restarting services, and performing any runtime configuration changes,
before moving on to do the same thing on the next instance. At any time
during the process, only one of the cluster's nodes will be unavailable.

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

To upgrade from BDR-Always-ON to PGD-Always-ON, run `tpaexec
reconfigure`:

```
$ tpaexec reconfigure ~/clusters/speedy\
  --architecture PGD-Always-ON\
  --pgd-proxy-routing local
```

This command will read config.yml, work out the changes necessary to
upgrade the cluster, and write a new config.yml. For details of its
invocation, see [the command's own
documentation](tpaexec-reconfigure.md). After reviewing the
changes, run `tpaexec upgrade` to perform the upgrade.
(`tpaexec upgrade` will automatically run `tpaexec provision` for you.) The upgrade
process does the following:

1. Checks that there are no witness nodes or version mismatches which
   would prevent the upgrade from working.
2. For each instance in the cluster:
    - Ensure that it has the right repositories available to install the
      software required for PGD-Always-ON.
    - Stop harp-manager.
    - Install pgd-proxy.
    - Stop Postgres and update packages.
    - Restart harp-manager; this will restart Postgres on the instance.
    - Wait for BDR consensus to be reached before continuing.
3. Update the BDR configuration on each instance.
4. Stop harp-proxy and set up pgd-proxy to replace it.
5. Restart pgbouncer on any pgbouncer instances.
6. Remove harp-manager and harp-proxy.
7. Upgrade pgd-cli.


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
