---
description: Upgrading your TPA cluster.
---

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

!!! Note "Minor version upgrades only"

**`tpaexec upgrade` does NOT support MAJOR version upgrades of Postgres.**

What TPA can upgrade is dependent on architecture:

-   The M1 architecture and all applicable failover managers for M1, `upgrade` will perform minor version upgrades of Postgres only.
-   With PGD architectures, `upgrade` will perform minor version upgrades of Postgres and the BDR extension.
-   With PGD architectures, and only in combination with the `reconfigure` command, `upgrade` can perform major-version upgrades of the BDR extension.

Support for upgrading other cluster components is planned for future releases.
!!!

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

To upgrade from BDR-Always-ON to PGD-Always-ON (that is, from BDR3/4 to
PGD5), first run `tpaexec reconfigure`:

```bash
$ tpaexec reconfigure ~/clusters/speedy\
  --architecture PGD-Always-ON\
  --pgd-proxy-routing local
```

This command will read config.yml, work out the changes necessary to
upgrade the cluster, and write a new config.yml. For details of its
invocation, see [the command's own
documentation](tpaexec-reconfigure.md). After reviewing the
changes, run `tpaexec upgrade` to perform the upgrade:

```bash
$ tpaexec upgrade ~/clusters/speedy\
```

Or to run the upgrade with proxy monitoring enabled,

```bash
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

## Upgrading from PGD-Always-ON to PGD-X

Upgrading a `PGD-Always-ON` cluster to `PGD-X` is a **significant
architectural evolution**, involving changes beyond a simple **software
update**. It is a _carefully orchestrated, multi-stage process_ that
requires reconfiguring your cluster in distinct phases before the final
software upgrade can take place. The procedure first modernizes your
`PGD 5` cluster's connection handling by replacing `pgd-proxy` with the
built-in `Connection Manager`, and then transitions the cluster to the
new `PGD-X` architecture.

The upgrade process transitions the cluster through three distinct states:

1.  **Start:** `PGD` 5.9+ (`PGD-Always-ON`) using `PGD-Proxy`
2.  **Intermediate:** `PGD` 5.9+ (`PGD-Always-ON`) now using the built-in `Connection Manager`
3.  **Final:** `PGD` 6 (`PGD-X Architecture`)

### Prerequisites

Before you begin, ensure you have met the following requirements:

-   **Cluster Version:** Your cluster must be running `PGD` version 5.9 or
    later. If you are on an earlier 5.x version, use `tpaexec upgrade`
    to upgrade to the latest minor version first. See the section
    (#pgd-always-on) for details on minor version upgrade of a PGD-Always-ON
    cluster.

-   **Backup:** You have a current, tested backup of your cluster.

-   **Review Overrides:** You have reviewed your `config.yml` for any
    instance-level proxy overrides (e.g., `pgd_proxy_options`). These
    cannot be migrated automatically and will require manual
    intervention.

-   **Co-hosted Proxies:** Your `PGD 5` cluster must be configured with
    co-hosted proxies (where the `pgd-proxy` role is on the same
    instance as the `bdr` role). Standalone proxy instances are **not
    supported** by this upgrade path.

### Stage 1: Migrating to the Built-in Connection Manager

The first stage is to reconfigure your `PGD 5.9+` cluster to switch
from using the external `pgd-proxy` to the modern, built-in
`Connection Manager`.

!!! Note Transitional State Only

This process creates a transitional `PGD 5.9+` cluster state that is
intended only as an intermediate step before upgrading to `PGD 6`.
TPA does not currently support using `tpaexec upgrade` on this
specific `Connection Manager` configuration. A future TPA release
will fully support lifecycle management of `PGD 5` with
`Connection Manager`.
!!!

!!! Warning Significant Manual Operations Required

This stage involves significant manual intervention on your live
cluster to apply the configuration changes. If you are not
comfortable performing these steps, we recommend waiting for a
future TPA release that will fully automate this process.
!!!

#### Step 1.1: Reconfigure for Connection Manager

Run the following command to update your `config.yml` file. This adds
the settings required to enable the built-in `Connection Manager`.

**This action only modifies the configuration file; it does not change
the running state of your database cluster yet.**

Before writing the new version, `reconfigure` automatically saves a
backup of the current file (e.g., `config.yml.~1~`), providing a safe
restore point.

For details of its invocation, see [the
command's own documentation](tpaexec-reconfigure.md).

```bash
$ tpaexec reconfigure ~/clusters/speedy --enable-connection-manager
```

#### Step 1.2: Apply the Configuration and Activate Connection Manager

Apply the configuration changes to your live cluster. This is a
**manual** operational task that involves, adding Postgres configuration
parameter, stopping the `pgd-proxy` service and restarting `PostgreSQL`
nodes in a rolling fashion to activate the `Connection Manager`.

For the detailed, step-by-step instructions for this process, please
follow the official [Connection Manager Migration
Guide](https://www.enterprisedb.com/docs/pgd/latest/upgrades/manual_overview/#pgd-5---moving-from-pgd-proxy-to-connection-manager).

### Stage 1 Complete

At the end of this stage, you will have a `PGD` cluster running with
the built-in `Connection Manager`. This is an intermediate state, and you
should proceed directly to Stage 2. While `tpaexec upgrade` for minor
version upgrades is **not supported** in this intermediate state, we
also advise agaist running `tpaexec deploy` until the upgrade to PGD 6
is complete.

### Stage 2: Upgrading the Architecture to PGD-X

Once your cluster is running with the `Connection Manager`, you can
proceed with the final configuration step to prepare for the `PGD 6`
upgrade.

!!! Note

You **must** start this process from a cluster that has successfully
completed `Stage 1` and is running with the built-in `Connection
Manager`.
!!!

#### Step 2.1: Reconfigure for the PGD-X Architecture

Run the following command to update your `config.yml` for the new
architecture. This changes the cluster architecture type, sets the `BDR`
version to 6, and removes any obsolete legacy settings.

**This action only modifies the configuration file; it does not change
the running state of your database cluster yet.**

```bash
$ tpaexec reconfigure ~/clusters/speedy --architecture PGD-X
```

#### Step 2.2: Perform the Software Upgrade

After reviewing the final changes in `config.yml`, you can now run the
standard `tpaexec upgrade` command. This will perform the software
upgrade on all nodes, bringing your cluster to `PGD 6`.

```bash
$ tpaexec upgrade ~/clusters/speedy
```

Or to run the upgrade with proxy monitoring enabled,

```bash
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
    - Fences the node off so there are no connections to it.
    - Stops, updates, and restarts postgres, including replacing PGD5
      with PGD6.
    - Unfences the node so it can receive connections again.
    - Updates pgbouncer and pgd-cli, as applicable for this node.
4. Applies BDR configuration specifically for BDR v6

### Upgrade Complete

Your cluster is now running `PGD 6` with the `PGD-X` architecture and is
fully manageable with both `tpaexec deploy` and `tpaexec upgrade` as
usual.

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
4. Finally, mark the server as "ready" again to receive requests through
   haproxy.

PGD logical standby or physical replica instances are updated without
any haproxy or pgbouncer interaction. Non-Postgres instances in the
cluster are left alone.

## M1

!!! Note
The M1 architecture only supports minor version upgrades of Postgres.
All applicable failover managers for M1 can run minor version upgrades
of Postgres.

Minor upgrade of other software component will be added in a future release.
!!!

For M1 clusters, `upgrade` will first update the streaming
replicas and witness nodes when applicable, then perform a [switchover](tpaexec-switchover.md)
from the primary to one of the upgraded replicas, update the primary, and
switchover back to the initial primary node.

## Controlling the upgrade process

You can control the order in which the cluster's instances are upgraded
by defining the `update_hosts` variable:

```bash
$ tpaexec upgrade ~/clusters/speedy \
  -e update_hosts=quirk,keeper,quaver
```

This may be useful to minimise lead/shadow switchovers during the upgrade
by listing the active PGD primary instances last, so that the shadow
servers are upgraded first.

If your environment requires additional actions, the
[postgres-pre-update and postgres-post-update hooks](tpaexec-hooks.md)
allow you to execute custom Ansible tasks before and after the package
installation step.

## Upgrading a Subset of Nodes

You can perform a rolling upgrade on a subset of instances by setting the `update_hosts` variable. However, support for this feature varies by architecture.

-   For the **M1** architecture, this feature is supported in all its upgrade scenarios.

-   For **PGD-Always-ON/BDR-Always-ON**, this is supported **only** during minor version upgrades.

### Best Practice for PGD-Always-ON/BDR-Always-ON

When performing a minor upgrade on a subset of PGD nodes, it is highly recommended to update the **RAFT leader nodes last**. This strategy avoids potential issues with post-upgrade checks while the cluster is running mixed versions of BDR.

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

```bash
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
