# Configuring HARP

TPAexec will install and configure HARP when `failover_manager` is set
to `harp`, which is the default for BDR-Always-ON clusters.

By default, TPAexec will install HARP v2, but you can still
[install and configure HARP v1](harp1.md) (deprecated)
by setting `harp_version: 1` explicitly.

## Installing HARP

You must provide the `harp-manager` and `harp-proxy` packages. Please
contact EDB to obtain access to these packages.

## Configuring HARP 

See the [HARP documentation](https://documentation.enterprisedb.com/harp/release/latest/configuration/)
for more details on HARP configuration. At present, TPAexec does not
expose the majority of HARP configuration parameters as variables, but
this will change in future releases.

Variable | Default value | Description
---- | ---- | ---
`harp_consensus_protocol` | `etcd` | The consensus layer to use (`etcd` or `bdr`)
`harp_location` | `location` | The location of this instance (defaults to the `location` parameter)

## Consensus layer

By default, TPAexec will set `harp_consensus_protocol: etcd`, and
install and configure etcd on the BDR instances.

HARP v2 requires etcd v3.5.0 or above, which is not available in the
default package repositories for any distribution. You must provide the
`harp-etcd` and `harp-etcdctl` packages; otherwise, TPAexec can download
and install etcd v3.5.0 from the Github release tarball if you specify

```
cluster_vars:
  etcd_packages:
    Debian: []
    RedHat: []
```

You can configure the following parameters for etcd:

Variable	| Default value	| Description
---|---|---
etcd_peer_port	| 2380	| The port used by etcd for peer communication
etcd_client_port	| 2379	| The port used by clients to connect to etcd

You can set `harp_consensus_protocol: bdr` instead, in which case the
existing BDR instances will be used for consensus, and no further
configuration is required.
