---
description: How TPA configures and secures etcd.
---

# etcd

`etcd` is a distributed, reliable key-value store commonly used for distributed
coordination. TPA configures `etcd` primarily as the Distributed Configuration
Store (DCS) when using Patroni as the failover manager for PostgreSQL clusters.

TPA automatically deploys and configures a 3-node `etcd` cluster by default when
you enable Patroni in the M1 architecture.

## Installation

TPA installs the `etcd` package available from the configured system
repositories. On SLES and RHEL-based systems, TPA automatically enables the PGDG
`extras` repository to provide the `etcd` package.

## etcd package version

By default, TPA installs the latest available version of etcd.

The version of the etcd package that is installed can be specified
by including `etcd_package_version: xxx` under the `cluster_vars`
section of the `config.yml` file.

```yaml
cluster_vars:
    …
    etcd_package_version: '3.6.2*'
    …
```

You may use any version specifier that apt or yum would accept.

If your version does not match, try prepending a `*` wildcard. This
is often necessary when the package version has an epoch qualifier
like `2:...`.

## Configuration

TPA generates the `/etc/etcd/etcd.conf` file based on your `config.yml` settings
and cluster topology. It configures peer and client communication URLs, data
directory, and SSL certificates.

## Security

TPA provides robust options for securing communication with and within the
`etcd` cluster. This is controlled primarily by the `etcd_ssl_enabled` and
`etcd_authentication_mode` variables.

### TLS Encryption

Setting `etcd_ssl_enabled: true` enables TLS encryption for all `etcd` traffic.
TPA will automatically:

* Generate a Cluster CA and server certificates (including appropriate IP and
  DNS Subject Alternative Names) for each etcd node.
* Configure etcd to use HTTPS for both peer-to-peer and client-server
  communication.
* Configure clients (`etcdctl`, Patroni) to connect via HTTPS and validate the
  server certificate using the CA.

### Client Authentication

Once TLS encryption is enabled (`etcd_ssl_enabled: true`), you can choose an
authentication mode using the `etcd_authentication_mode` variable:

* **`none` (default):** No client authentication is performed. Communication
  relies solely on TLS encryption if `etcd_ssl_enabled` is `true`.
* **`basic`:** Requires clients to authenticate using a username and password.
  TPA automatically:

  * Creates an administrative `root` user with a generated password.
  * If using Patroni, creates a dedicated, least-privilege user for Patroni
    (configurable via `patroni_etcd_user`) with `readwrite` access only to its
    specific key prefix (e.g., `/tpa/cluster_name`).
  * Configures Patroni to use these dedicated credentials.
* **`mtls`:** Requires clients (including peer nodes) to present a valid TLS
  certificate signed by the trusted cluster CA. TPA automatically:

  * Configures `etcd` to require and validate client certificates for both peer
    (`ETCD_PEER_CLIENT_CERT_AUTH=true`) and client
    (`ETCD_CLIENT_CERT_AUTH=true`) connections.
  * Configures clients (`etcdctl`, Patroni) to present their client certificates
    for authentication.

!!! Note
TPA includes robust logic to handle transitions between different
authentication modes during deployment or reconfiguration, ensuring the
cluster remains stable. Configuration validation checks are performed early to
prevent invalid combinations (e.g., `mtls` requires `etcd_ssl_enabled: true`).
However, it's currently not able to handle transition of values for
`etcd_ssl_enabled` (i.e. from `false` to `true` or vice-versa).
This limitation also makes it impossible to switch from any `etcd_authentication_mode` that requires a different `etcd_ssl_enabled` value such as `basic` to `mtls` (or `mtls` to `basic`).
Clusters deployed using TPA version below 23.41.0 defaulted to `etcd_ssl_enabled: false` and won't be able to modify `etcd_ssl_enabled`. 
!!!

## Configuration Variables

You can set the following variables for `etcd`.

| Variable | Default value | Description |
| ----- | ----- | ----- |
| `etcd_peer_port` | `2380` | The TCP port `etcd` uses for peer-to-peer (server-to-server) communication. |
| `etcd_client_port` | `2379` | The TCP port `etcd` uses for client communication. |
| `etcd_ssl_enabled` | `false`\* | Enable SSL/TLS encryption for all `etcd` communication. See Security. \* `true` for new clusters via `tpaexec configure`. |
| `etcd_authentication_mode` | `none`\* | Defines the client authentication mode (`none`, `basic`, `mtls`). Requires `etcd_ssl_enabled: true` for modes other than `none`. See Security. \* `mtls` for new clusters via `tpaexec configure`. |
| `etcd_compaction_mode` | `revision` | The automatic compaction mode (`revision` or `periodic`). |
| `etcd_compaction_retention` | `10` | The retention value for automatic compaction. For `revision` mode, this is the number of revisions to keep. For `periodic` mode, this is the time interval (e.g., `1h`). |

## Minor update for etcd using `tpaexec upgrade`

!!! Warning ETCDCTL_API v2 is deprecated
  etcd v3.4 introduced a breaking change, making ETCDCTL_API v3 the default version, but allowed the
  v2 API to be enabled manually.

  etcd v3.6 completely removed the `--enable-v2` flag, making it impossible to use the v2 API at all.

  TPA upgrade ONLY supports upgrade of `etcd` versions using the v3 API.

  Before using TPA to upgrade `etcd` in a cluster, ensure it has
  [migrated from the v2 API to the v3 API](https://etcd.io/docs/v3.4/op-guide/v2-migration/)
!!!

When trying to upgrade to a specific package version, ensure the `etcd_package_version` in
`config.yml` is updated to reflect the desired version.

The desired version can also be passed as an extra argument to the `tpaexec upgrade` command with:

```shell
tpaexec upgrade -e etcd_package_version="<desired version>" --components=etcd
```

Refer to the section on
[package version selection and upgrade](tpaexec-upgrade.md#package-version-selection) for more
information.

To select etcd for upgrade, ensure the `--components` flag passed to the `tpaexec upgrade` command
contains `etcd` (or `all`)

Refer to the section on [component selection for upgrade](tpaexec-upgrade.md#component-selection)
for more information.
