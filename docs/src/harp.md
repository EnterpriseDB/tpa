# Configuring HARP

TPA installs and configures HARP when `failover_manager` is set
to `harp`. This value is the default for BDR-Always-ON clusters.

## Installing HARP

You must provide the `harp-manager` and `harp-proxy` packages.
Contact EDB to obtain access to these packages.

## Configuring HARP

See the [HARP documentation](https://documentation.enterprisedb.com/harp/release/latest/configuration/)
for more details on HARP configuration.

Variable | Default value | Description
---- | ---- | ---
`cluster_name` | `` | The name of the cluster.
`harp_consensus_protocol` | ` ` | The consensus layer to use (`etcd` or `bdr`).
`harp_location` | `location` | The location of this instance (defaults to the `location` parameter).
`harp_ready_status_duration` | `10` | Amount of time in seconds the node's readiness status persists if not refreshed.
`harp_leader_lease_duration` | `6` | Amount of time in seconds the Lead Master lease persists if not refreshed.
`harp_lease_refresh_interval` | `2000` | Amount of time in milliseconds between refreshes of the Lead Master lease.
`harp_dcs_reconnect_interval` | `1000` | The interval, measured in ms, between attempts that a disconnected node tries to reconnect to the DCS.
`harp_dcs_priority` | `500` | In the case in which two nodes have an equal amount of lag and other qualified criteria to take the Lead Master lease, acts as an additional ranking value to prioritize one node over another.
`harp_stop_database_when_fenced` | `false` | Rather than removing a node from all possible routing, stop the database on a node when it's fenced.
`harp_fenced_node_on_dcs_failure` | `false` | If HARP is unable to reach the DCS, then fence the node.
`harp_maximum_lag` | `1048576` | Highest allowable variance (in bytes) between last recorded LSN of previous Lead Master and this node before being allowed to take the Lead Master lock.
`harp_maximum_camo_lag` | `1048576` | Highest allowable variance (in bytes) between last received LSN and applied LSN between this node and its CAMO partners.
`harp_camo_enforcement` | `lag_only` | Whether to strictly enforce CAMO queue state.
`harp_use_unix_sock` | `false` | Use Unix domain socket for manager database access.
`harp_request_timeout` | `250` | Time in milliseconds to allow a query to the DCS to succeed.
`harp_watch_poll_interval` | `500` | Milliseconds to sleep between polling DCS. Applies only when `harp_consensus_protocol` is `bdr`.
`harp_proxy_timeout` | `1` | Builtin proxy connection timeout, in seconds, to Lead Master.
`harp_proxy_keepalive` | `5` | Amount of time builtin proxy waits on an idle connection to the Lead Master before sending a keepalive ping.
`harp_proxy_max_client_conn` | `75` | Maximum number of client connections accepted by harp-proxy (`max_client_conn`).
`harp_ssl_password_command` | None | A custom command to receive the obfuscated sslpassword in the stdin and provide the handled sslpassword via stdout.
`harp_db_request_timeout`| `10s` | Similar to dcs -> request_timeout but for connection to the database.

You can use the
[harp-config hook](tpaexec-hooks.md#harp-config)
to execute tasks after the HARP configuration files are
installed, for example, to install additional configuration files.

## Consensus layer

The `--harp-consensus-protocol` argument to `tpaexec configure` is
mandatory for the BDR-Always-ON architecture.

### etcd

If the `--harp-consensus-protocol etcd` option is given to `tpaexec
configure`, then TPA sets `harp_consensus_protocol` to `etcd`
in `config.yml`. It gives the `etcd` role to a suitable subset of the
instances, depending on your chosen layout.

HARP v2 requires etcd v3.5.0 or later, which is available in the
products/harp/release package repositories provided by EDB.

You can configure the following parameters for etcd,

Variable	| Default value	| Description
---|---|---
etcd_peer_port	| 2380	| The port used by etcd for peer communication
etcd_client_port	| 2379	| The port used by clients to connect to etcd

### bdr

If the `--harp-consensus-protocol bdr` option is given to `tpaexec
configure`, then TPA sets `harp_consensus_protocol` to `bdr`
in `config.yml`.  In this case, the existing PGD instances are used
for consensus, and no further configuration is required.

## Configuring a separate user for HARP proxy

If you want HARP proxy to use a separate read-only user, you can specify that
by setting `harp_dcs_user: username` under `cluster_vars`. TPA uses the
`harp_dcs_user` setting to create a read-only user and set it up in the DCS
configuration.

## Configuring a separate user for HARP manager

If you want HARP manager to use a separate user, you can specify that by setting `harp_manager_user: username` under `cluster_vars`. TPA uses that setting to create a new user and grant it the `bdr_superuser` role.

## Custom SSL password command

The command provided by `harp_ssl_password_command` is used by HARP
to de-obfuscate the `sslpassword` given in the connection string. If
`sslpassword` isn't present, then `harp_ssl_password_command` is
ignored. If `sslpassword` isn't obfuscated, then
`harp_ssl_password_command` isn't required and should not be specified.

## Configuring the HARP service

You can configure the following parameters for the HARP service.

Variable	| Default value	| Description
---|---|---
`harp_manager_restart_on_failure`	| `false`	| If `true`, the `harp-manager` service is overridden so it's restarted on failure. The default is `false` to comply with the service installed by the `harp-manager` package.

## Configuring HARP http(s) health probes

You can enable and configure the http(s) service for HARP that
provides API endpoints to monitor the service's health.

Variable	| Default value	| Description
---|---|---
`harp_http_options`| <br>`enable: false`<br>`secure: false`<br>`host: <inventory_hostname>`<br>`port: 8080`<br>`probes:`<br>&nbsp;&nbsp;`timeout: 10s`<br>`endpoint: "host=<proxy_name> port=<6432> dbname=<bdrdb> user=<username>"`| Configure the http section of HARP `config.yml` that defines the http(s) API settings.|

The variable can contain these keys:
```
enable: false
secure: false
cert_file: "/etc/tpa/harp_proxy/harp_proxy.crt"
key_file: "/etc/tpa/harp_proxy/harp_proxy.key"
host: <inventory_hostname>
port: 8080
probes:
  timeout: 10s
endpoint: "<valid dsn>"
```

The `cert_file` and `key_file` keys are both required if you use `secure: true`
and are willing to use your own certificate and key.

You must ensure that both certificate and key are available at the given
location on the target node before running `deploy`.

Leave both `cert_file` and `key_file` empty if you want TPA to generate a
certificate and key for you using a cluster-specific CA certificate.
TPA CA certificate isn't "well-known." You need to add this certificate
to the trust store of each machine that probes the endpoints.
The CA certificate can be found on the cluster directory on the TPA node at
`<cluster_dir>/ssl/CA.crt` after `deploy`.

See the [HARP documentation](https://documentation.enterprisedb.com/harp/release/latest/) for more information about the available API endpoints.