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

You can use the
[pgd-proxy-config hook](tpaexec-hooks.md#pgd-proxy-config)
to execute tasks after the PGD PROXY configuration files have been
installed (e.g., to install additional configuration files).

### bdr_node_groups

Group-level options related to pgd-proxy can be set under
`bdr_node_groups` along with other node group options:

```yaml
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

```yaml
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

```yaml
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
```yaml
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

### pgd_proxy_service_environment

The `pgd-proxy` process is started by systemd, which does not pass a
user's ambient environment through to the service. `pgd-proxy` relies on
libpq to connect to Postgres, so it needs a couple of libpq environment
variables to find its password file and to require TLS. TPA sets these
in the systemd unit file via `pgd_proxy_service_environment`, which
defaults to:

```yaml
pgd_proxy_service_environment:
  PGPASSFILE: '{{ pgd_proxy_home }}/.pgpass'
  PGSSLMODE: 'require'
```

Each key/value pair is rendered as an `Environment=KEY=VALUE` line in
`/etc/systemd/system/pgd-proxy.service`.

You can override this under `cluster_vars` (for all proxies) or under a
pgd-proxy instance's `vars`:

```yaml
cluster_vars:
  pgd_proxy_service_environment:
    PGPASSFILE: /etc/edb/pgd-proxy/.pgpass
    PGSSLMODE: require
```

Note that the value you supply *replaces* the default mapping in full;
it is not merged key by key. If you override this variable to change one
entry, include every entry you still want — for example, keep
`PGSSLMODE: require` when changing only `PGPASSFILE`, otherwise
`pgd-proxy` falls back to libpq's default `sslmode`.

## Updating pgd-proxy using `tpaexec upgrade`

When trying to upgrade to a specific package version, ensure the `pgd_proxy_package_version` in
`config.yml` is updated to reflect the desired version. This version should be kept in line with
the `bdr_package_version` and `pgdcli_package_version` versions specified for the cluster.
Defining `bdr_package_version` and omitting `pgd_proxy_package_version` and `pgdcli_package_version`
from `config.yml` will ensure the same value is used across all three components.

The desired version can also be passed as an extra argument to the `tpaexec upgrade` command with:

```shell
tpaexec upgrade <cluster_dir> \
  -e pgd_proxy_package_version="<desired version>" \
  --components=pgd-proxy
```

Refer to the section on
[package version selection and upgrade](tpaexec-upgrade.md#package-version-selection) for more
information.

To select pgd-proxy for upgrade, ensure the `--components` flag passed to the `tpaexec upgrade`
command contains `pgd-proxy` (or `all`)

Refer to the section on [component selection for upgrade](tpaexec-upgrade.md#component-selection)
for more information.
