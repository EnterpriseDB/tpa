# Configuring repmgr

TPA installs repmgr on all Postgres instances that have the
`failover_manager` instance variable set to `repmgr`. This is the
default setting.

The directory of the `repmgr` configuration file defaults to
`/etc/repmgr/<version>`, where `<version>` is the major version
of Postgres being installed on this instance. You can
change it by setting the `repmgr_conf_dir` variable for the instance.
The configuration file is always called `repmgr.conf`.

The default repmgr configuration sets up automatic failover
between instances configured with the role primary and the role
replica.

## repmgr configuration

You can set the following instance variables:

- `repmgr_priority` sets `priority` in the config file.
- `repmgr_location` sets `location ` in the config file.
- `repmgr_reconnect_attempts` sets `reconnect_attempts` in the config file, default `6`.
- `repmgr_reconnect_interval` sets `reconnect_interval` in the config file, default `10`.
- `repmgr_use_slots` sets `use_replication_slots` in the config file, default `1`.
- `repmgr_failover` sets `failover` in the config file, default `automatic`.

Any extra settings in `repmgr_conf_settings` are also passed through
into the repmgr config file.

## repmgr on PGD instances

On PGD instances, `repmgr_failover` is set to `manual` by default.
