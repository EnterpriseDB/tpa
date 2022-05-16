# Configuring HARP

TPAexec will install and configure HARP when `failover_manager` is set
to `harp`, which is the default for BDR-Always-ON clusters.

## Installing HARP

You must provide the `harp-manager` and `harp-proxy` packages. Please
contact EDB to obtain access to these packages.

## Configuring HARP

See the [HARP documentation](https://documentation.enterprisedb.com/harp/release/latest/configuration/)
for more details on HARP configuration.

Variable | Default value | Description
---- | ---- | ---
`cluster_name` | `` | The name of the cluster.

`harp_consensus_protocol` | `bdr` | The consensus layer to use (`etcd` or `bdr`)
`harp_location` | `location` | The location of this instance (defaults to the `location` parameter)
`harp_ready_status_duration` | `10` | Amount of time in seconds the node's readiness status will persist if not refreshed.
`harp_leader_lease_duration` | `6` | Amount of time in seconds the Lead Master lease will persist if not refreshed.
`harp_lease_refresh_interval` | `2000` | Amount of time in milliseconds between refreshes of the Lead Master lease.
`harp_dcs_reconnect_interval` | `1000` | The interval, measured in ms, between attempts that a disconnected node tries to reconnect to the DCS.
`harp_dcs_priority` | `500` | In the case two nodes have an equal amount of lag and other qualified criteria to take the Lead Master lease, this acts as an additional ranking value to prioritize one node over another.
`harp_stop_database_when_fenced` | `false` | Rather than simply removing a node from all possible routing, stop the database on a node when it is fenced.
`harp_fenced_node_on_dcs_failure` | `false` | If HARP is unable to reach the DCS then fence the node.
`harp_maximum_lag` | `1048576` | Highest allowable variance (in bytes) between last recorded LSN of previous Lead Master and this node before being allowed to take the Lead Master lock.
`harp_maximum_camo_lag` | `1048576` | Highest allowable variance (in bytes) between last received LSN and applied LSN between this node and its CAMO partner(s).
`harp_camo_enforcement` | `lag_only` | Whether CAMO queue state should be strictly enforced.
`harp_use_unix_sock` | `false` | Use unix domain socket for manager database access.
`harp_request_timeout` | `250` | Time in milliseconds to allow a query to the DCS to succeed.
`harp_watch_poll_interval` | `500` | Milliseconds to sleep between polling DCS.  Only applies when `harp_consensus_protocol` is `bdr`.
`harp_proxy_timeout` | `1` | Builtin proxy connection timeout, in seconds, to Lead Master.
`harp_proxy_keepalive` | `5` | Amount of time builtin proxy will wait on an idle connection to the Lead Master before sending a keepalive ping.

## Consensus layer

By default, TPAexec will set `harp_consensus_protocol: bdr`, but if you
set it to `etcd` instead, it can install and configure etcd on the BDR
instances.

HARP v2 requires etcd v3.5.0 or above, which is available in the
products/harp/release package repositories provided by EDB.

You can configure the following parameters for etcd:

Variable	| Default value	| Description
---|---|---
etcd_peer_port	| 2380	| The port used by etcd for peer communication
etcd_client_port	| 2379	| The port used by clients to connect to etcd

You can set `harp_consensus_protocol: bdr` instead, in which case the
existing BDR instances will be used for consensus, and no further
configuration is required.

## Configuring a separate user for harp proxy

If you want harp proxy to use a separate readonly user, you can specify that
by setting `harp_dcs_user: username` under cluster_vars. TPAexec will use
`harp_dcs_user` setting to create a readonly user and set it up in the DCS
configuration.
