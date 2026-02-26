---
description: How to install and configure EFM with TPA.
---

# Configuring EFM

TPA will install and configure EFM when `failover_manager` is set to
`efm`.

The version of EFM to be used can be configured by changing the `efm_version`:

```yaml
cluster_vars:
  …
  failover_manager: efm
  efm_version: 5.2
  …
```
It can also be defined when executing `tpaexec configure`:

```shell
tpaexec configure my-cluster-dir -a M1 --failover_manager efm --efm-version 5.2
```

Note that EFM is only available via EDB's package repositories
and requires a valid subscription.

## EFM configuration

TPA will generate `efm.nodes` and `efm.properties` with the appropriate
instance-specific settings, with remaining settings set to the respective
default values. TPA will also place an `efm.notification.sh` script which
basically contains nothing by default and leaves it up to the user to fill it
in however they want. TPA will override the default settings for
`auto.allow.hosts` and `stable.nodes.file` to simplify adding agents
to the cluster.

See the [EFM documentation](https://www.enterprisedb.com/docs/efm/latest/)
for more details on EFM configuration.

## efm_user_password_encryption

Must be either `scram-sha-256` or `md5`

Set `efm_user_password_encryption` to control the `auth-method` for the
`efm` Postgres user's `auth-method` in `pg_hba.conf` as well as the algorithm
used when generating its encrypted password.

!!! Note
    The default value for `efm_user_password_encryption` is `scram-sha-256` for new clusters.

```yaml
efm_user_password_encryption: 'scram-sha-256' # or can be set to `md5`
```

## efm_conf_settings

You can use `efm_conf_settings` to set specific parameters.
These must be written as entries in an Ansible dictionary, in `key: value` form

See the [documentation on the `efm.properties` file](https://www.enterprisedb.com/docs/efm/latest/04_configuring_efm/01_cluster_properties/)
for details on which settings can be configured.

```yaml
cluster_vars:
  efm_conf_settings:
     notification.level: WARNING
     ping.server.ip: <well known address in network>
```

If you make changes to values under `efm_conf_settings`, TPA will always
restart EFM to activate the changes.

### EFM witness

TPA will install and configure EFM as witness on instances whose `role`
contains `efm-witness` (when using EFM, you can also use the role `witness`, as it gets implicitly converted to `efm-witness`). 
For such instances the `upstream` property must be specified to point
to the designated primary database instance.

### Repmgr

EFM works as a failover manager and therefore TPA will still install
repmgr for setting up postgresql replicas on postgres versions 11 and
below. `repmgrd` i.e. repmgr's daemon remains disabled in this case and
repmgr's only job is to provided replication setup functionality.

For postgres versions 12 and above, any cluster that uses EFM will use
`pg_basebackup` to create standby nodes and not use repmgr in any form.

### Node Promotability

TPA determines whether a node is eligible for promotion by EFM during
failover based on the node's role and replication topology. The following
rules are applied when generating the EFM configuration:

- **Witness nodes** (`efm-witness` role) are never promotable.
- **Nodes with the `efm-not-promotable` role** are not eligible for
  promotion. This can be used to prevent specific standbys, such as DR or
  reporting nodes, from being promoted to primary.
- **Cascading standbys** (nodes that are not directly replicating from the
  primary) are also not promotable.
- All other nodes are considered promotable by default.

To explicitly prevent a standby from being promoted, add
`efm-not-promotable` to the node’s `roles` list in your cluster
configuration. This ensures that EFM will not attempt to promote this node during
failover events.

## Minor update for EFM using `tpaexec upgrade`

!!! Note EFM is _not_ a package update
  Due to how EFM versions are released, each EFM minor version has its own package (`edb-efm49` for
  v4.9, `edb-efm50` for v5.0, etc.)
  which installs its own distinct binary and configuration directories.
!!!

When upgrading EFM, set the `efm_version` in `config.yml` to reflect the desired version.

TPA installs the package for the new version and copies over the configuration files from the
existing EFM version's configuration directory into the new EFM version's configuration directory, 
and removes the existing EFM version's package, service file and binary directory for cleanup.

Because EFM upgrade depends on a previous version being installed and configured (the source), TPA
first checks to ensure this is true. In the event a source EFM version is not installed (it's binary
directory does not exist) or not configured (it's configuration directory does not exist), the
upgrade will exit with an error. When running the upgrade, if the target EFM version (specified by
`efm_version` in the `config.yml`) already has a binary directory and configuration directory,
upgrade skips over EFM as it is already installed and configured to the desired version.

!!! Note
  EFM upgrade is supported from EFM 4.9 to 5.0 even if not a minor upgrade
  per say, no additional steps are required for this upgrade to happen.
!!!

To select EFM for upgrade, ensure the `--components` flag passed to the
`tpaexec upgrade` command contains `efm` (or `all`)

Refer to the section on [component selection for upgrade](tpaexec-upgrade.md#component-selection)
for more information.

!!! Note
  EFM can't work in a mixed version environment. Due to this limitation, there is no good reason to
  support a partial upgrade of the EFM component.
  TPA will **always** upgrade the EFM software on the complete set of EFM nodes when `efm` is part
  of the list of components to upgrade.
  TPA will ignore `update_hosts` when deciding which nodes should have EFM upgraded.
!!!
