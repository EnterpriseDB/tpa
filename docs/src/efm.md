---
description: How to install and configure EFM with TPA.
---

# Configuring EFM

TPA will install and configure EFM when `failover_manager` is set to
`efm`.

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
used when generating it's encrypted password.

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
contains `efm-witness`.

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

- **Witness nodes** (`witness` role) are never promotable.
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
