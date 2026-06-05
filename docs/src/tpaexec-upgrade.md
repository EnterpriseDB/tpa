---
description: Upgrading your TPA cluster.
---

# Upgrading your cluster

The `tpaexec upgrade` command is used to upgrade the software running on
your TPA cluster (`tpaexec deploy` will not perform upgrades).

(This command replaces the earlier `tpaexec update-postgres` command.)

!!! Note
TPA does not yet support using the `tpaexec upgrade` command for clusters
that have shared Barman and/or shared PEM configurations, and will add
this functionality in a future release.
!!!

## Introduction

If you make any changes to config.yml, the way to apply those changes is
to run `tpaexec provision` followed by `tpaexec deploy`.

The exception to this rule is that `tpaexec deploy` will refuse to
install a different version of a package that is already installed.
Instead, you must use `tpaexec upgrade` to perform software upgrades.

The following components are able to be upgraded for **any** architecture:

- Postgres
- [PgBouncer](pgbouncer.md#minor-update-for-pgbouncer-using-tpaexec-upgrade)
- [Barman](barman.md#minor-update-using-tpaexec-upgrade)
- [PG Backup API](pg-backup-api.md#minor-update-for-pg-backup-api-using-tpaexec-upgrade)
- [PEM](pem.md#minor-update-for-pem-using-tpaexec-upgrade)
(both server and agent)

The following components are able to be upgraded on **M1** architectures and
depend on the failover manager used:

- [EFM](efm.md#minor-update-for-efm-using-tpaexec-upgrade)
- [Patroni](patroni.md#minor-update-for-patroni-using-tpaexec-upgrade)
- [etcd](etcd.md#minor-update-for-etcd-using-tpaexec-upgrade) (for Patroni)
- [repmgr](repmgr.md#minor-update-for-repmgr-using-tpaexec-upgrade)

The following components are able to be upgraded on **BDR-Always-ON**/**PGD-Always-ON**
architectures, depending on the BDR version used:

- [pgdcli](pgd-cli.md#updating-pgd-cli-using-tpaexec-upgrade) (v1 for BDR 4,
v5 for PGD5)
- [pgd-proxy](pgd-proxy.md#updating-pgd-proxy-using-tpaexec-upgrade) (only for PGD5)

!!! Note Minor version upgrades only
**`tpaexec upgrade` does NOT support MAJOR version upgrades of Postgres and most cluster components**
What TPA can upgrade is dependent on architecture:

- The M1 architecture and all applicable failover managers for M1, `upgrade` can perform minor
version upgrades of `Postgres`, the corresponding failover manager (`EFM`, `Patroni` or `repmgr`)
and any non-architecture specific components that are selected.
- With PGD architectures, `upgrade` will perform minor version upgrades of Postgres and the BDR
extension as well as `pgd-cli` and `pgd-proxy` if they are explicitly opted-in.
- With PGD architectures, and only in combination with the `reconfigure` command, `upgrade` can
perform major-version upgrades of the BDR extension.

Support for upgrading other cluster components was added in TPA `v23.41.0`
_Certain components (such as `EFM`) are an exception. Consult the `upgrade` section of each
component's documentation for further information._
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

When upgrading a cluster to PGD-Always-ON, upgrading an existing
PGD-Always-ON cluster, or performing a minor upgrade of a PGD-S or
PGD-X cluster, you can enable monitoring of the status of your
proxy nodes during the upgrade by adding the option
`-e enable_proxy_monitoring=true` to your `tpaexec upgrade` command
line. If enabled, this will create an extra table in the bdr database
and write monitoring data to it while the upgrade takes place. The
performance impact of enabling monitoring is very small and it is
recommended that it is enabled.

## Before you upgrade

This section describes the checks you should perform on your cluster
before running `tpaexec upgrade`. Working through these in order will
catch most common problems before they affect a live cluster.

### Verify cluster health

The upgrade is easiest to perform on a cluster that is in a known-good
state. Run `tpaexec test <cluster>` to exercise the standard health
checks. The upgrade process itself runs pre-upgrade health checks, but
discovering a problem ahead of time gives you longer to address it.

For any BDR enabled architecture, also confirm that all nodes appear in
its catalogue:

```sql
SELECT node_name, peer_state_name, peer_target_state_name
  FROM bdr.node_summary;
```

Every entry should report `ACTIVE` (or `STANDBY` for read-only
standbys). Investigate any other state before proceeding.

For M1 clusters using repmgr, run `repmgr cluster show` on the primary
and confirm every node is shown as running and connected.

### Verify backups

Before any upgrade, confirm that a recent Barman backup exists and is
in a state from which you could restore. On the Barman host:

```shell
sudo -u barman barman list-backup <server>
sudo -u barman barman check <server>
```

Any failed status here should be investigated before starting. Once
the upgrade is underway, the Barman WAL receiver is stopped, so the
backup landscape during the upgrade window is fixed at whatever
existed beforehand.

### Verify replication lag

Whilst the cluster may be healthy at a high level, individual replicas
may be lagging. The upgrade fences each instance in turn; if a replica
is significantly behind, it will take longer to catch up after being
unfenced, and the overall upgrade duration will grow.

For PGD clusters:

```sql
SELECT slot_name, active, restart_lsn, write_lag, flush_lag, replay_lag
  FROM bdr.node_slots;
```

For M1 clusters, on the primary:

```sql
SELECT application_name, state, write_lag, flush_lag, replay_lag
  FROM pg_stat_replication;
```

Aim for lag measured in seconds, not minutes. Investigate any replica
that is seriously behind before starting.

### Pin and review package versions

For control over what is installed during the upgrade, it is recommended
that you explicitly set package versions  in `config.yml` before running
`tpaexec upgrade`. The relevant variables are `postgres_package_version`,
`bdr_package_version`, `pgd_proxy_package_version`,
`pgdcli_package_version`, and the component-specific equivalents.

Without an explicit pin, TPA installs the latest available package for
each component, which can result in an unintended major-version
upgrade. See [Package version selection](#package-version-selection)
for details.

!!! Note
After updating versions in `config.yml`, run `tpaexec provision` to
regenerate the inventory.
!!!

### Read the release notes

Check the release notes for the target versions of every component you
are upgrading. EDB's PGD and Postgres release notes occasionally call
out version-specific upgrade considerations: settings that must be
changed before or after the upgrade, deprecations, and behaviour
changes. The same applies to TPA's own release notes for any newer
version of TPA you may be using to perform the upgrade.

### Plan the maintenance window

`tpaexec upgrade` processes the cluster instance-by-instance. The
upgrade is rolling: at any one time only a single instance is fenced
off. However, the total wall-clock time depends on the cluster size,
the number of components being upgraded, and the storage and network
characteristics of each instance.

We recommend running the same upgrade against a staging copy of the
cluster first to measure the duration, then choosing a maintenance
window that covers that time with a comfortable buffer.

### Disable scheduled jobs

Anything scheduled to run against the cluster during the upgrade
window should be paused. Typical items:

- Cron jobs that hit the database (analytics, reporting).
- External backup tools that are not aware of the upgrade.
- Long-running migrations or batch jobs.

TPA itself stops the Barman WAL receiver before starting and restarts
it afterwards; you do not need to disable Barman manually.

### Test the upgrade in a staging environment

We strongly recommend reproducing the upgrade in a non-production
environment that matches your production cluster's architecture,
Postgres flavour and version, package pinnings, and any custom hooks.
This catches surprises (missing packages in your configured
repository, unexpected configuration drift) before they affect live
traffic.

## During the upgrade

This section describes what to expect whilst `tpaexec upgrade` is
running and what to watch for from outside TPA.

### What to expect

TPA processes the cluster one instance at a time. For each instance,
in turn, the upgrade:

1. Fences the instance off so the proxy or failover manager stops
   sending it new connections.
2. Stops the affected services on that instance.
3. Installs the new packages.
4. Updates configuration files where required.
5. Restarts services and waits for them to come up.
6. Unfences the instance.

You should expect brief connection interruptions whilst each instance is
fenced and again when it returns to service. Applications using
connection pooling and retry logic should typically not see
client-visible errors during these transitions.

Whilst each non-leader node is being upgraded, write traffic
continues through the current write leader. Each time the write
leader itself is upgraded, a brief leader-election interruption
occurs. PGD-S and PGD-X arrange for the write leader to be upgraded
last; PGD-Always-ON upgrades nodes in inventory order, so a leader
election occurs whenever the current leader's turn comes round.

### Default order of upgrades

By default, `tpaexec upgrade` visits affected hosts in **inventory
order**, with one architecture-specific exception: PGD-S and PGD-X
automatically upgrade the current write leader **last**.

- **PGD-Always-ON, BDR-Always-ON, PGD-Lightweight:** all Postgres/BDR
  nodes in inventory order (excluding PEM servers), then all
  pgd-proxy nodes in inventory order.
- **PGD-S, PGD-X:** all BDR data nodes except the current write
  leader (inventory order), then the write leader.
- **M1 with repmgr / EFM / Patroni:** replicas (and witnesses, for
  repmgr) first in inventory order, then a switchover so the
  original primary becomes a replica, then the original primary,
  then a switchover back. For Patroni, etcd nodes and the Patroni
  package itself are upgraded after the Postgres rolling phase.

The M1 EFM upgrade itself always runs on every EFM node, regardless
of `update_hosts`, because mixing EFM versions across data nodes is
not supported.

To restrict the upgrade to a subset of these hosts, or to sequence
the upgrade across multiple invocations (for example, to upgrade
shadow servers in one run and the active PGD primary in a later
run), see [Controlling the upgrade
process](#controlling-the-upgrade-process).

### What to watch from the application side

Whilst the upgrade is running, a brief pause at each fence/unfence
transition is normal. Sustained connection failures across multiple
instances are not — if you see those, stop and investigate before TPA
proceeds to the next instance.

If an application is running against the cluster during the upgrade,
monitor:

- Application error rates: transient retries are expected; sustained
  errors are not.
- Connection pool metrics: brief drops in available connections are
  expected.
- Replication slot lag: may grow transiently as each instance catches
  up post-upgrade.

## After the upgrade

This section describes the verification you should perform once
`tpaexec upgrade` has completed.

### Verify installed package versions

Confirm that the new packages are installed on every instance. On
RHEL-family hosts:

```shell
tpaexec cmd <cluster> all -m shell -a 'rpm -qa | grep -E "^(postgres|edb-)"'
```

On Debian / Ubuntu hosts:

```shell
tpaexec cmd <cluster> all -m shell -a 'dpkg -l | grep -E "(postgres|edb-)"'
```

The same package versions should be reported on every instance of the
same role.

### Verify services and replication

Confirm that all services restarted cleanly:

```shell
tpaexec cmd <cluster> all -m shell -a 'systemctl is-active postgres'
```

For PGD clusters, confirm that BDR has fully reconverged:

```sql
SELECT node_name, peer_state_name FROM bdr.node_summary;
```

For M1 clusters with repmgr:

```shell
tpaexec cmd <cluster> role_primary -m shell -a 'repmgr -f /etc/repmgr.conf cluster show'
```

### Take a fresh backup

After any non-trivial upgrade, take a fresh Barman backup of the
cluster:

```shell
tpaexec cmd <cluster> role_barman -m shell -a 'sudo -u barman barman backup <server>'
```

This gives you a known-good restore point that reflects the
post-upgrade state.

### Re-enable scheduled jobs

If you disabled cron jobs, batch jobs, or external scheduled tasks
before the upgrade, re-enable them now. TPA's own Barman WAL receiver
is restarted automatically.

### Run tpaexec test

As a final smoke check, run the standard test suite:

```shell
tpaexec test <cluster>
```

This exercises connectivity, replication, role mapping, and the
component-specific checks that ran before the upgrade. A clean test
run is the simplest end-to-end confirmation that the upgrade landed.

## Recovering from a failed upgrade

If `tpaexec upgrade` reports a failure, the cluster is left in a known
state at whichever instance was being processed when the failure
occurred. Subsequent instances are not touched.

### When to roll back, when to call EDB Support

A roll-back is only safe before TPA has applied any non-reversible
catalogue change — typically the BDR-side configuration updates that
occur in major-version upgrades. Once those changes are in place, the
correct path is forward, not backward.

If you are unsure whether to proceed or roll back, stop and contact
EDB Support with:

- The `ansible.log` from the failed run.
- The output of `tpaexec test <cluster>`.
- A description of which instances completed the upgrade and which
  did not.

## Common pitfalls

This section consolidates a few specific situations that have caught
users out in the past.

### Pinned package versions cause no-op upgrades

If `postgres_package_version` (or any other `xxx_package_version`)
already matches the installed package, `tpaexec upgrade` reports the
components as "already at the desired version" and does nothing. The
symptom is a run that completes quickly with no changes, and the
desired version not installed.

Fix: update `config.yml` to set the new desired version, then re-run
`tpaexec provision` followed by `tpaexec upgrade`. See [Package
version selection](#package-version-selection) for details.

### Shared Barman or shared PEM clusters

TPA does not currently support running `tpaexec upgrade` against
clusters with shared Barman or shared PEM configurations. The
restriction is enforced by the upgrade's preconditions, which abort
early. Until support is added, upgrades for these cluster shapes
need to be performed manually outside TPA — see [After a manual
major-version Postgres upgrade](reconciling-local-changes.md#after-a-manual-major-version-postgres-upgrade)
for how to reconcile the cluster afterwards.

## Component selection

!!! Note
Upgrading components is strictly opt-in
!!!

By default, `tpaexec upgrade` will update Postgres alone if the `--components` flag is not passed

```shell
tpaexec upgrade ~/clusters/speedy
```

To select specific components to update, the `--components` flag takes a comma-separated list

```shell
tpaexec upgrade ~/clusters/speedy \
   --components=postgres,pgd-proxy,pgdcli,pgbouncer,pg-backup-api,barman
```

If all applicable components in the cluster should be updated, `all` can be passed to the flag

```shell
tpaexec upgrade --components=all
```

|component|value|architecture|
|---------|-----|------------|
|Barman|barman|all|
|PEM|pem-server,pem-agent|all|
|PgBackupAPI|pg-backup-api|all|
|PgBouncer|pgbouncer|all|
|EFM|efm|M1 with `failover_manager=efm`|
|etcd|etcd|M1 with `failover_manager=patroni`|
|Patroni|patroni|M1 with `failover_manager=patroni`|
|RepMgr|repmgr|M1 with `failover_manager=repmgr`|
|PGD Cli|pgdcli|BDR-Always-ON, PGD-Always-ON |
|PGD-Proxy|pgd-proxy|PGD-Always-ON|
|Postgres,EPAS,PGE|postgres|All|
|All|all|All|

## Package version selection

By default, `tpaexec upgrade` will update to the latest
available versions of the installed packages if you did not explicitly
specify any package versions (e.g., Postgres, PGD, or pglogical) when
you created the cluster.

!!! Note Minor upgrade is not strictly enforced
If a desired package version is NOT provided when upgrading, TPA will install the latest available
package.
The minor version restriction is NOT strictly enforced during tpaexec upgrade.
This can result in unwillingly attempting an unsupported major upgrade of a
component.
Thus, it is recommended to explicitly select versions for upgrade to ensure compatibility in the
existing cluster.
Postgres does not pose this issue since major versions are different packages altogether which stops
this from happening.
!!!

If you did select specific versions, for example by using any of the `--xxx-package-version` options
(e.g., postgres, bdr, pglogical) to [`tpaexec configure`](tpaexec-configure.md), or by defining
`xxx_package_version` variables in config.yml, the upgrade will do nothing because the installed
packages already satisfies the requested versions.

In this case, you must edit config.yml, update the version settings, and re-run `tpaexec provision`.
The update will then install the selected version of the packages. You can also update to a specific
version by specifying versions on the command line as shown below:

```shell
tpaexec upgrade ~/clusters/speedy -vv      \
  --components=postgres,pgbouncer          \
  -e postgres_package_version="16.10*"     \
  -e pgbouncer_package_version="1.24*"     \
  -e bdr_package_version="5.9.0*"
```

Please note that version syntax here depends on your OS distribution and package manager. In
particular, yum accepts `*xyz*` wildcards, while apt only understands `xyz*` (as in the example
above).

!!! Note: see limitations of using wildcards in package_version in
[tpaexec-configure](tpaexec-configure.md#known-issue-with-wildcard-use).
!!!

It is your responsibility to ensure that the combination of Postgres, PGD, and pglogical package
versions that you request are sensible. That is, they should work together, and there should be an
upgrade path from what you have installed to the new versions.

For PGD clusters, it is a good idea to explicitly specify exact versions for all three components
(Postgres, PGD, pglogical) rather than rely on the package manager's dependency resolution to select
the correct dependencies.

We strongly recommend testing the upgrade in a QA environment before running it in production.

## Configuration

In certain cases, minor-version upgrades do not need changes to config.yml.
If no `postgres_package_version` is defined in `config.yml`, when `tpaexec upgrade`
is run, it will upgrade Postgres to the latest available minor-version in a graceful 
way (what exactly that means depends on the details of the cluster).

For control over minor-version upgrades of other components, it is recommended
to ensure a specific `xxx_package_version` is specified in `config.yml` before
running `tpaexec upgrade` and explicitly opting-in to upgrade specific components
using the `--components=x,y,z` flag (or `--components=all` to upgrade all, as
applicable to the cluster). Running `tpaexec upgrade` and opting in to upgrade
some or all components WITHOUT pinning their `xxx_package_version` in `config.yml`
could result in a major version upgrade of installed component packages, which
TPA does not support as it may break compatibility.

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

```shell
tpaexec reconfigure ~/clusters/speedy\
  --architecture PGD-Always-ON\
  --pgd-proxy-routing local
```

This command will read config.yml, work out the changes necessary to
upgrade the cluster, and write a new config.yml. For details of its
invocation, see [the command's own
documentation](tpaexec-reconfigure.md). After reviewing the
changes, run `tpaexec upgrade` to perform the upgrade:

```shell
tpaexec upgrade ~/clusters/speedy\
```

Or to run the upgrade with proxy monitoring enabled,

```shell
tpaexec upgrade ~/clusters/speedy\
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
software upgrade can take place. The procedure first modernises your
`PGD 5` cluster's connection handling by replacing `pgd-proxy` with the
built-in `Connection Manager`–a step that currently requires manual
operations on the live cluster but is planned for automation in a future
TPA release–and then transitions the cluster to the new `PGD-X`
architecture.

The upgrade process transitions the cluster through three distinct states:

1. **Start:** `PGD` 5.9+ (`PGD-Always-ON`) using `PGD-Proxy`
2. **Intermediate:** `PGD` 5.9+ (`PGD-Always-ON`) now using the built-in `Connection Manager`
3. **Final:** `PGD` 6 (`PGD-X Architecture`)

### Prerequisites

Before you begin, ensure you have met the following requirements:

- **Cluster Version:** Your cluster must be running `PGD` version 5.9 or
later. If you are on an earlier 5.x version, use `tpaexec upgrade`
to upgrade to the latest minor version first. See the section
(#pgd-always-on) for details on minor version upgrade of a PGD-Always-ON
cluster.

- **Backup:** You have a current, tested backup of your cluster.

- **Review Overrides:** You have reviewed your `config.yml` for any
instance-level proxy overrides (e.g., `pgd_proxy_options`). These
cannot be migrated automatically and will require manual
intervention.

- **Co-hosted Proxies:** Your `PGD 5` cluster must be configured with
co-hosted proxies (where the `pgd-proxy` role is on the same
instance as the `bdr` role). The presence of standalone proxy
instances will cause the `switch2cm` command to abort. You must
remove standalone proxy instances from your cluster before
proceeding with the migration.

### Stage 1: Migrating to the Built-in Connection Manager

The first stage is to reconfigure your `PGD 5.9+` cluster to switch
from using the external `pgd-proxy` to the modern, built-in
`Connection Manager`. TPA provides the `tpaexec switch2cm` command to
automate this migration with minimal downtime.

!!! Note Transitional State Only
This process creates a transitional `PGD 5.9+` cluster state that is
intended only as an intermediate step before upgrading to `PGD 6`.
TPA does not currently support staying in `PGD5.9+` with `Connection Manager`
enabled or moving to a newer minor version of `PGD5.9+` with this configuration.
A future TPA release will fully support lifecycle management of `PGD 5` with
`Connection Manager`.
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

```shell
tpaexec reconfigure ~/clusters/speedy --enable-connection-manager
```

#### Step 1.2: Switch to Connection Manager

Run the `tpaexec switch2cm` command to perform the migration from
`pgd-proxy` to the built-in `Connection Manager`. This command
automatically runs `tpaexec provision` to update the Ansible inventory,
then switches all nodes with minimal downtime:

```shell
tpaexec switch2cm ~/clusters/speedy
```

The `switch2cm` command performs the following operations:

1. Updates the Ansible inventory with Connection Manager settings
2. For each node:
   - Fences the node to prevent new connections
   - Restarts PostgreSQL to load the Connection Manager configuration
   - Stops the `pgd-proxy` service
   - Restarts PostgreSQL again to allow Connection Manager to bind ports
   - Waits for Connection Manager to start listening
   - Unfences the node and verifies connectivity

This process follows the official [EDB Connection Manager Migration
procedure](https://www.enterprisedb.com/docs/pgd/latest/upgrades/manual_overview/#pgd-5---moving-from-pgd-proxy-to-connection-manager).

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

```shell
tpaexec reconfigure ~/clusters/speedy --architecture PGD-X
```

#### Step 2.2: Perform the Software Upgrade

After reviewing the final changes in `config.yml`, you can now run the
standard `tpaexec upgrade` command. This will perform the software
upgrade on all nodes, bringing your cluster to `PGD 6`.

```shell
tpaexec upgrade ~/clusters/speedy
```

Or to run the upgrade with proxy monitoring enabled,

```shell
tpaexec upgrade ~/clusters/speedy\
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

## PGD-S or PGD-X

When upgrading an existing PGD6 (PGD-S or PGD-X) cluster to the latest available
software versions, the upgrade process does the following:

1. Checks that the cluster is healthy and that the nodes are listening
   on the configured ports.
2. Checks that the nodes to be upgraded have their repositories
   configured and updated, including local repositories.
3. Checks that updated packages can be installed
4. Upgrade each BDR node in the cluster one at a time:

   **Important:** To ensure high availability, if the write leader is among the
   nodes being upgraded, it will be the very last node to be upgraded.

   - Fences the node off so it doesn't accept connections
   - Stops postgres
   - Updates postgres and PGD packages
   - Unfences the node so it can receive connections again
   - Checks that the BDR cluster has re-established Raft consensus
   - Checks that the upgraded node is listening on the configured ports
5. Re-runs the cluster health checks
6. Outputs information about the upgraded packages

## PGD-Always-ON

When upgrading an existing PGD-Always-ON (PGD5) cluster to the latest available
software versions, the upgrade process does the following:

1. Checks that all preconditions for upgrading the cluster are
   met, including that it is not a shared PEM or shared Barman cluster.
2. Runs pre-upgrade health checks for all components, as applicable to the cluster,
   including that no Barman backup is underway (this stops the WAL-receiver)
3. For each instance in the cluster, checks that it has the correct
   repositories configured and that the required postgres packages are
   available in them.
4. Checks that all selected components are able to be updated to the
   desired version (if a package version is provided)
5. For each BDR node in the cluster, one at a time:
   - Fences the node off to ensure that pgd-proxy doesn't send any
   connections to it.
   - Stops, updates, and restarts postgres.
   - Unfences the node so it can receive connections again.
   - Updates pgd-proxy and pgd-cli software (if explicitly opted-in)
6. For the applicable nodes in the cluster, updates pgbouncer, barman, pg-backup-api, and PEM
   agents/PEM server (according to the node's roles)
7. Starts the Barman WAL-receiver if required and runs post-upgrade health checks for all components
   (as applicable to the cluster)

## BDR-Always-ON

For BDR-Always-ON clusters, the upgrade process goes through the cluster instances
one by one and does the following:

1. Checks that all preconditions for upgrading the cluster are
   met, including that it is not a shared PEM or shared Barman cluster.
2. Runs pre-upgrade health checks for all components, as applicable to the cluster,
   including that no Barman backup is underway (this stops the WAL-receiver)
3. For each instance in the cluster, checks that it has the correct
   repositories configured and that the required postgres packages are
   available in them.
4. Tell haproxy the server is under maintenance.
5. If the instance was the active server, request pgbouncer to reconnect
   and wait for active sessions to be closed.
6. Stop Postgres, update Postgres, etcd, and pgdcli (if applicable and opted-in) packages and restart
   Postgres.
7. Finally, mark the server as "ready" again to receive requests through
   haproxy.
8. For the applicable nodes in the cluster, updates pgbouncer, barman, pg-backup-api, and PEM
   agents/PEM server (according to the node's roles)
9. Starts the Barman WAL-receiver if required and runs post-upgrade health checks for all components
   (as applicable to the cluster)

PGD logical standby or physical replica instances are updated without
any haproxy or pgbouncer interaction. Non-Postgres instances in the
cluster are left alone.

## M1

For M1 clusters, `upgrade` will first update the streaming
replicas and witness nodes when applicable, then perform a [switchover](tpaexec-switchover.md)
from the primary to one of the upgraded replicas, update the primary, and
switchover back to the initial primary node.

1. Checks that all preconditions for upgrading the cluster are
   met, including that it is not a shared PEM or shared Barman cluster.
2. Runs pre-upgrade health checks for all components, as applicable to the cluster,
   including that no Barman backup is underway (this stops the WAL-receiver)
3. For each instance in the cluster, checks that it has the correct
   repositories configured and that the required postgres packages are
   available in them.
4. Update Postgres on the streaming replicas and witness. nodes (when applicable)
5. Perform a [switchover](tpaexec-switchover.md) from the primary to one of the upgraded replicas
6. Update Postgres on the primary
7. Switchover back to the initial primary node.
8. For the applicable nodes in the cluster, updates pgbouncer, barman, pg-backup-api, and PEM
   agents/PEM server (according to the node's roles)
9. Starts the Barman WAL-receiver if required and runs post-upgrade health checks for all components
   (as applicable to the cluster)

## Controlling the upgrade process

You can control the order in which the cluster's instances are upgraded
by defining the `update_hosts` variable:

```shell
tpaexec upgrade ~/clusters/speedy \
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

You can perform a rolling upgrade on a subset of instances by setting the `update_hosts` variable.
However, support for this feature varies by architecture.

- For the **M1** architecture, this feature is fully supported for `repmgr` and `Patroni` managed clusters.
`EFM` managed clusters respect the `update_hosts` list for all components _except_ EFM. All data nodes
will upgrade their EFM version regardless of the nodes specified in `update_hosts` as EFM does not
support clusters running different versions across data nodes.

- For **PGD-Always-ON/BDR-Always-ON**, this is supported **only** during minor version upgrades.

### Best Practice for PGD-Always-ON/BDR-Always-ON

When performing a minor upgrade on a subset of PGD nodes, it is highly recommended to update the **RAFT leader nodes last**. This strategy avoids potential issues with post-upgrade checks while the cluster is running mixed versions of BDR.

### PGD-S and PGD-X

`tpaexec upgrade` arranges for the current write leader to be
upgraded last in PGD-S and PGD-X clusters automatically: the
Postgres/PGD rolling phase is split into two `serial: 1` plays, one
for every BDR data node except the current write leader and one for
the write leader itself. No additional steps are required to achieve
the leader-last sequence on these architectures.
