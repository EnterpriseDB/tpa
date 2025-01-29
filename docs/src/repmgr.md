---
description: How to install and configure repmgr with TPA.
---

# repmgr

TPA will install repmgr on all postgres instances that have the
`failover_manager` instance variable set to `repmgr`; this is the
default setting.

The directory of the `repmgr` configuration file defaults to
`/etc/repmgr/<version>`, where `<version>` is the major version
of postgres being installed on this instance, but can be
changed by setting the `repmgr_conf_dir` variable for the instance.
The configuration file itself is always called `repmgr.conf`.

The default repmgr configuration will set up automatic failover
between instances configured with the role `primary` and the role
`replica`.

## repmgr package version

By default, TPA installs the latest available version of repmgr.

The version of the repmgr package that is installed can be specified 
by including `repmgr_package_version: xxx` under the `cluster_vars` 
section of the `config.yml` file.

```yaml
cluster_vars:
    …
    repmgr_package_version: '4.0.5-1.pgdg90+1'
    …
```

You may use any version specifier that apt or yum would accept.

If your version does not match, try appending a `*` wildcard. This
is often necessary when the package version has an epoch qualifier
like `2:...`.

## repmgr configuration

The following instance variables can be set:

`repmgr_priority`: sets `priority` in the config file
`repmgr_location`: sets `location ` in the config file
`repmgr_reconnect_attempts`: sets `reconnect_attempts` in the config file, default `6`
`repmgr_reconnect_interval`: sets `reconnect_interval` in the config file, default `10`
`repmgr_use_slots`: sets `use_replication_slots` in the config file, default `1`
`repmgr_failover`: sets `failover` in the config file, default `automatic`

Any extra settings in `repmgr_conf_settings` will also be passed through
into the repmgr config file.

## repmgr on PGD instances

On PGD instances, `repmgr_failover` will be set to `manual` by default.
