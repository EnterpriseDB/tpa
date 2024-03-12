# Configuring pgd-proxy

TPA installs and configures pgd-proxy for the PGD-Always-ON
architecture with PGD 5 on any instance with `pgd-proxy` in its `role`.

(By default, the [PGD-Always-ON architecture](architecture-PGD-Always-ON.md)
runs pgd-proxy on all the data nodes in every location. You
can instead create any number of additional proxy instances with
`--add-proxy-nodes-per-location 3`.)

## Configuration

pgd-proxy is configured at PGD level by way of SQL functions.

Hash | Function | Description
---- | ---- | ----
`pgd_proxy_options` | `bdr.alter_proxy_option()` | pgd-proxy configuration, for example, port
`bdr_node_groups` | `bdr.alter_node_group_option()` | Configuration for the proxy's node group, for example, `enable_proxy_routing`
`bdr_node_options` | `bdr.alter_node_option()` | Routing configuration for individual PGD nodes

See the [PGD documentation](https://www.enterprisedb.com/docs/pgd/latest/) for more details.

### bdr_node_groups

You can set group-level options related to pgd-proxy under
`bdr_node_groups` along with other node group options:

```
cluster_vars:
  bdr_node_groups:
  - name: group1
    options:
      enable_proxy_routing: true
```

You must explicitly set `enable_proxy_routing` to `true` to enable pgd-proxy for the group.

### bdr_node_options

You can set node-level options related to pgd-proxy under
`bdr_node_options` on any PGD instance:

```
instances:
- Name: first
  vars:
    bdr_node_options:
      route_priority: 42
```

### pgd_proxy_options

You can set options for a pgd-proxy instance, rather than the group or nodes
it's attached to. Set these options under `default_pgd_proxy_options` under
`cluster_vars` (which applies to all proxies) or under
`pgd_proxy_options` on any pgd-proxy instance:

```
cluster_vars:
  default_pgd_proxy_options:
    listen_port: 6432

instances:
- Name: someproxy
  vars:
    pgd_proxy_options:
      listen_port: 9000
```

In this case, while other instances get their `listen_port` setting from
`cluster_vars`, `someproxy` overrides that default setting and configures its 
own `listen_port` in the instance's `vars` section.

### PGD proxy http(s) health probes

You can enable and configure the http(s) service for a PGD proxy that
provides API endpoints to monitor the proxy's health.

`pgd_http_options` under `cluster_vars` or instance `vars` stores
all the settings that define the http(s) API. These settings are under the `http`
subsection of the `proxy` top section of `pgd-proxy-config.yml`.

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
The TPA CA certificate isn't "well-known." You need to add this certificate
to the trust store of each machine that probes the endpoints.
You can find the CA certificate on the cluster directory on the TPA node at:
`<cluster_dir>/ssl/CA.crt` after `deploy`.

See the [pgd-proxy documentation](https://www.enterprisedb.com/docs/tpa/latest/reference/pgd-proxy/) for more information on the available API endpoints.
