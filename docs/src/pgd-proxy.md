---
description: Incorporating pgd-proxy into your TPA deployed PGD 5 cluster.
---
# pgd-proxy

## pgd-proxy package version

By default, TPA installs the latest available version of `pgd-proxy`.

The version of the `pgd-proxy` package that is installed can be specified 
by including `pgd_proxy_package_version: xxx` under the `cluster_vars` 
section of the `config.yml` file.

```yaml
cluster_vars:
    …
    pgd_proxy_package_version: '5.0.0-1'
    …
```

You may use any version specifier that apt or yum would accept.

If your version does not match, try appending a `*` wildcard. This
is often necessary when the package version has an epoch qualifier
like `2:...`.

## Configuring pgd-proxy

TPA will install and configure pgd-proxy for the PGD-Always-ON
architecture with PGD 5 on any instance with `pgd-proxy` in its `role`.

(By default, the [PGD-Always-ON architecture](architecture-PGD-Always-ON.md)
will run `pgd-proxy` on all the data nodes in every location, but you
can instead create any number of additional proxy instances with
`--add-proxy-nodes-per-location 3`.)

## Configuration

`pgd-proxy` is configured at PGD level via SQL functions.

Hash | Function | Description
---- | ---- | ----
`pgd_proxy_options` | `bdr.alter_proxy_option()` | pgd-proxy configuration, e.g. port
`bdr_node_groups` | `bdr.alter_node_group_option()` | configuration for the proxy's node group, e.g. `enable_proxy_routing`
`bdr_node_options` | `bdr.alter_node_option()` | routing configuration for individual PGD nodes

See the PGD documentation for more details.

### bdr_node_groups

Group-level options related to pgd-proxy can be set under
`bdr_node_groups` along with other node group options:

```
cluster_vars:
  bdr_node_groups:
  - name: group1
    options:
      enable_proxy_routing: true
```

Note that `enable_proxy_routing` must be explicitly set to `true` for pgd-proxy to be enabled for the group.

### bdr_node_options

Node-level options related to pgd-proxy can be set under
`bdr_node_options` on any PGD instance:

```
instances:
- Name: first
  vars:
    bdr_node_options:
      route_priority: 42
```

### pgd_proxy_options

Options for a pgd-proxy instance itself, rather than the group or nodes
it is attached to, can be set under `default_pgd_proxy_options` under
`cluster_vars` (which applies to all proxies), or under
`pgd_proxy_options` on any pgd-proxy instance:

```
cluster_vars:
  default_pgd_proxy_options:
    listen_port: 6432
    read_listen_port: 6433

instances:
- Name: someproxy
  vars:
    pgd_proxy_options:
      listen_port: 9000
      read_listen_port: 9001
```

In this case, while other instances will get their `listen_port` setting from
`cluster_vars`, `someproxy` overrides that default setting and configures its 
own `listen_port` in the instances' `vars` section.

### PGD proxy http(s) health probes

You can enable and configure the http(s) service for PGD proxy that will
provide api endpoints to monitor the proxy's health.

`pgd_http_options` under `cluster_vars` or instance `vars` will store
all the settings that defines the http(s) api which live under the `http`
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
certificate and key for you using a cluster specific CA certificate.
TPA CA certificate won't be 'well known', you will need to add this certificate
to the trust store of each machine that will probe the endpoints.
The CA certificate can be found on the cluster directory on the TPA node at:
`<cluster_dir>/ssl/CA.crt` after `deploy`.

see pgd-proxy documentation for more information on the available api endpoints.
