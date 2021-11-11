# Configuring HARP

HARP v1 is deprecated, and should not be used. Unless you are trying to
diagnose a problem with an existing HARP v1 installation, please use
[HARP v2](harp.md) instead.

TPAexec will install and configure HARP when `failover_manager` is set to
`harp`. You must also set `harp_version: 1` explicitly to use HARP v1.

Note that HARP currently only supports BDR instances.

## HARP configuration

TPAexec will generate `/etc/bdr3/harp.ini` with the appropriate
instance-specific settings, with other settings set to the respective
default values.

See the [HARP documentation](https://documentation.enterprisedb.com/harp/release/latest/configuration/)
for more details on HARP configuration.

The following variables can be set for any HARP instance:

Variable | Default value | Description
---- | ---- | ----
`harp_consensus_protocol` | `bdr` | The consensus layer to use (`bdr` or `etcd`)
`harp_location` | `location` | The location of this instance (defaults to the `location` parameter)
`harp_allow_lead` | [1] | Indicates whether the node can take the Lead Master lock
`harp_safety_interval` | `100` | Time in milliseconds to require before routing to a newly promoted Lead Master is allowed
`harp_maximum_lag` | `1048576` | Highest allowable variance between last recorded LSN of previous Lead Master and this node, in bytes
`harp_maximum_camo_lag` | `1048576` | Highest allowable variance between last received LSN and applied LSN between this node and its CAMO partner(s), in bytes
`harp_lock_duration` | `15` | How many seconds the Lead Master lock will persist if not refreshed.
`harp_lock_interval` | `5` | Seconds between refreshes of the Lead Master lock.
`harp_external_lock_interval` | `0` | Seconds between refreshes of Lead Master locks for locations other than our own; `0` disables
`harp_listen_port` | `5442` | Port for HARP router to listen on

## Consensus layer configuration

HARP requires a consensus layer (sometimes known as DCS layer) to function.
This is set via `harp_consensus_protocol`, which currently can be one of `bdr`
(default) or `etcd`.

### BDR

No additional configuration is required if `harp_consensus_protocol` is set to `bdr`.
However a minimum of 3 (three) BDR nodes must be present for the BDR consensus
layer to be quorate.

### etcd

TPAexec will install and configure `etcd` on instances whose `role` contains
`etcd`.

If you want to use etcd for consensus, you must set `etcd_packages`
explicitly to specify which package to install.

```
cluster_vars:
  # …
  etcd_packages:
    Debian:
    - etcd
    RedHat: []
```

Note that currently no `etcd` packages are available for CentOS 8. If
you leave the package list empty, as above, TPAexec will install etcd
v3.5.0 from the latest Github release tarball. (This works on Debian
too, which has an older etcd package in the default repositories.)

The following variables can be set for any `etcd` instance:

Variable | Default value | Description
---- | ---- | ----
`etcd_peer_port` | 2380 | The port used by etcd for peer communication
`etcd_client_port` | 2379 | The port used by clients to connect to etcd

The `etcd` instance name (configuration item `ETCD_NAME`) is set to the
same value as the instance node name.

The `etcd` cluster will be initialised for nodes in the same location
(either `harp_location`, if set, otherwise `location`).
