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
`repmgr_location`: sets `location` in the config file
`repmgr_reconnect_attempts`: sets `reconnect_attempts` in the config file, default `6`
`repmgr_reconnect_interval`: sets `reconnect_interval` in the config file, default `10`
`repmgr_use_slots`: sets `use_replication_slots` in the config file, default `1`
`repmgr_failover`: sets `failover` in the config file, default `automatic`

Any extra settings in `repmgr_conf_settings` will also be passed through
into the repmgr config file.

## repmgr service configuration

`repmgr_service_environment`: sets environment variables to the repmgr service unit file. The environment variables
must be defined under the `repmgr_service_environment` variable, in a 'key-value' fashion (see example below).
You can use `repmgr_service_environment` to set any parameters, whether recognised by TPA or not. 
You need to quote the value exactly as it would appear in the `repmgrd.service` file.

```yaml
cluster_vars:
  repmgr_service_environment:
    LD_PRELOAD: '/usr/edb/pge15/lib/libpq.so.5:/usr/edb/pge15/lib/libpqagent86.so'
    AGENT86_SHARD_FILE: '/var/lib/pgsql/shard.dat'
```

On the repmgr service file:

```shell
root@kaput:~# cat /etc/systemd/system/repmgr.service
[Unit]
Description=Postgres replication manager
After=postgres-monitor.service
Wants=postgres-monitor.service

[Service]
Type=simple
User=postgres
Group=postgres
Environment=AGENT86_SHARD_FILE=/var/lib/pgsql/shard.dat
Environment=LD_PRELOAD=/usr/edb/pge15/lib/libpq.so.5:/usr/edb/pge15/lib/libpqagent86.so
StandardOutput=syslog
ExecStart=/usr/lib/postgresql/17/bin/repmgrd -f /etc/repmgr/17/repmgr.conf --verbose --daemonize=false
ExecStop=/bin/kill -TERM $MAINPID
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## repmgr on PGD instances

On PGD instances, `repmgr_failover` will be set to `manual` by default.

## Minor update for repmgr using `tpaexec upgrade`

!!! Warning `repmgr` minor-versioning is DIFFERENT: the THIRD digit (X.Y.**Z**) is the minor version
A minor release upgrade involves updating repmgr from one minor release to another minor release
within the same major release (e.g. 5.3.1 to 5.3.2).
An upgrade between minor releases of differing major releases (e.g. 5.2.1 to 5.3.2) is a MAJOR
upgrade.
TPA does NOT support major version upgrades of `repmgr`
!!!

When trying to upgrade to a specific package version, ensure the `repmgr_package_version` in `config.yml` is updated to reflect the desired version.

The desired version can also be passed as an extra argument to the `tpaexec upgrade` command with:

```shell
tpaexec upgrade <cluster_dir> \
    -e repmgr_package_version="<desired version>"\
    --components=repmgr
```

Refer to the section on
[package version selection and upgrade](tpaexec-upgrade.md#package-version-selection) for more
information.

To select repmgr for upgrade, ensure the `--components` flag passed to the `tpaexec upgrade` command
contains `repmgr` (or `all`)

Refer to the section on [component selection for upgrade](tpaexec-upgrade.md#component-selection)
for more information.
