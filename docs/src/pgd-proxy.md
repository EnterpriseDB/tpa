# Configuring pgd-proxy

TPA will install and configure pgd-proxy for the PGD-Always-ON
architecture with BDR 5 on any instance with `pgd-proxy` in its `role`.

(By default, the [PGD-Always-ON architecture](architecture-PGD-Always-ON.md)
includes standalone `pgd-proxy` instances in each location, but using
the `--cohost-proxies` configure option will install pgd-proxy on the
BDR instances instead.)

## Configuration

`pgd-proxy` is configured at BDR level via SQL functions.

Hash | Function | Description
---- | ---- | ----
`pgd_proxy_options` | `bdr.alter_proxy_option()` | pgd-proxy configuration, e.g. port
`bdr_node_groups` | `bdr.alter_node_group_option()` | configuration for the proxy's node group, e.g. `enable_proxy_routing`
`bdr_node_options` | `bdr.alter_node_option()` | routing configuration for individual BDR nodes

See the BDR documentation for more details.

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
`bdr_node_options` on any BDR instance:

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

instances:
- Name: someproxy
  vars:
    pgd_proxy_options:
      fallback_groups:
        - somegroup
```

In this case, `someproxy` ends up with the `listen_port` setting from
`cluster_vars` and its own `fallback_groups` setting. However, it could
also override the default `listen_port` by defining a different value
alongside `fallback_groups`; this instance-level setting would take
precedence over the defaults in `cluster_vars`.
