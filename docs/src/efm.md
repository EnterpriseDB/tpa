# Configuring EFM

TPA installs and configures EFM when `failover_manager` is set to
`efm`.

You need a valid subscription to EDB's package repositories
to obtain EFM packages.

## EFM configuration

TPA generates `efm.nodes` and `efm.properties` with the appropriate
instance-specific settings or default values. TPA also installs an `efm.notification.sh`
script, which does nothing by default. You can fill it in however you want.

See the [EFM documentation](https://www.enterprisedb.com/docs/efm/latest/)
for more details on configuring EFM.

## efm_conf_settings

You can use `efm_conf_settings` to set any parameters, whether or not 
TPA recognizes them. Where needed, you need to quote the value exactly as
you would if you were editing `efm.properties` manually:

```yaml
cluster_vars:
  efm_conf_settings:
     standby.restart.delay: 1
     application.name: quarry
     reconfigure.num.sync: true
     reconfigure.num.sync.max: 1
     reconfigure.sync.primary: true
```

If you change `efm_conf_settings`, TPA always
restarts EFM to activate the changes.

### EFM witness

TPA installs and configures EFM as a witness on instances whose `role`
contains `efm-witness`.

### Repmgr

EFM doesn't provide a way to create new replicas. TPA uses repmgr to 
create replicas for Postgres versions 11 and earlier. Although repmgr 
packages are installed in this case, the repmgrd daemon remains disabled when EFM is in use.

For Postgres versions 12 and later, any cluster that uses EFM uses
`pg_basebackup` to create standby nodes and doesn't use repmgr in any form.
