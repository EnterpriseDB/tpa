# Configuring EFM

TPAexec will install and configure EFM when `failover_manager` is set to
`efm`.

Note that EFM is only available via EnterpriseDB's package repositories
and requires a valid subscription.

## EFM configuration

TPAexec will generate `efm.nodes` and `efm.properties` with the appropriate
instance-specific settings, with remaining settings set to the respective
default values. TPAexec will also place an `efm.notification.sh` script which
basically contains nothing by default and leaves it up to the user to fill it
in however they want.

See the [EFM documentation](https://www.enterprisedb.com/docs/efm/latest/)
for more details on EFM configuration.

## efm_conf_settings

You can use `efm_conf_settings` to set any parameters, whether recognised
by TPAexec or not. Where needed, you need to quote the value exactly as it
would appear in `efm.properties`:

```yaml
cluster_vars:
  efm_conf_settings:
     standby.restart.delay: 1
     application.name: quarry
     reconfigure.num.sync: true
     reconfigure.num.sync.max: 1
     reconfigure.sync.primary: true
```

If you make changes to values under `efm_conf_settings`, TPAexec will always
restart EFM to activate the changes.

### EFM witness

TPAexec will install and configure EFM as witness on instances whose `role`
contains `efm-witness`.

### Repmgr

EFM works as a failover manager and therefore TPAexec will still install
repmgr for setting up postgresql replicas. `repmgrd` i.e. repmgr's daemon
remains disabled in this case and repmgr's only job is to provided replication
setup functionality.
