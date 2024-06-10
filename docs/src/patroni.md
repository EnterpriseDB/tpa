# Using Patroni as a Failover Manager

Patroni can be used as a single master failover manager with the M1
architecture using the following command options.

```shell
tpaexec configure cluster_name -a M1 --enable-patroni --postgresql 14
```

Or by setting the config.yml option

```yaml
cluster_vars:
  failover_manager: patroni
```

TPA is able to deploy Patroni clusters using either `patroni` packages (from
PGDG repositories) or `edb-patroni` packages (from EDB repositories). You can
configure that through the `patroni_package_flavour` option under `cluster_vars`
in the config.yml, which can also be set through the `--patroni-package-flavour`
command-line argument. If no `patroni_package_flavour` is explicitly set, TPA
will attempt to infere the flavour based on the configured repositories: if EDB
repositories were configured, implicitly select `edb` flavour, otherwise
implicitly select `community` flavour.

TPA `configure` will add 3 etcd nodes, and may add 2 haproxy nodes if you
specify the option `--enable-haproxy`. Etcd is used for the Distributed
Configuration Store (DCS). Patroni supports other DCS backends, but they are not
currently supported by EDB or TPA.

Alternative to HAProxy, you can use the `--enable-pgbouncer` option to configure
PgBouncer in the Postgres nodes. PgBouncer will be configured to pool
connections for the primary. Patroni will be configured to reconfigure PgBouncer
upon failovers or switchovers in the cluster, so PgBouncer follows the new
primary Postgres instance.

TPA uses Patroni's feature of converting an existing PostgreSQL cluster. This
allows for TPA to initialise and manage configuration. Once the PostgreSQL
cluster has been created, Patroni will take the management over. TPA will then
remove any postgres configuration files used during setup.

Once set up, Postgres can continue to be managed using TPA and settings
in `config.yml` for the cluster. You can also use Patroni interfaces,
such as the command line `patronictl` and the REST API, but it is
recommended to use TPA methods wherever possible.

# Configuration options

These configuration variables can be used to control certain behaviours
in the deployment of Patroni in TPA.

| Variable                        | Default value | Description                                                                                                                                                                                                                                                          |
|---------------------------------|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `patroni_super_user`            | postgres      | User to create in postgres for superuser role.                                                                                                                                                                                                                       |
| `patroni_replication_user`      | replicator    | Username to create in postgres for replication role.                                                                                                                                                                                                                 |
| `patroni_restapi_user`          | patroni       | Username to configure for the patroni REST API.                                                                                                                                                                                                                      |
| `patroni_rewind_user`           | rewind        | Username to create in postgres for pg_rewind function.                                                                                                                                                                                                               |
| `patroni_installation_method`   | pkg           | Install patroni from packages or source (e.g. git repo or local source directory if docker).                                                                                                                                                                         |
| `patroni_package_flavour`       | community if no EDB repository is configured, else edb | Whether to install `edb-patroni` package (`edb` flavour, requires EDB repositories) or `patroni` package (`community` flavour, requires PGDG and EPEL (RedHat based only) repositories). |
| `patroni_ssl_enabled`           | no            | Whether to enable SSL for REST API and ctl connection. Will use the cluster SSL cert and CA if available.                                                                                                                                                            |
| `patroni_rewind_enabled`        | yes           | Whether to enable postgres rewind, creates a user defined by patroni_rewind_user and adds config section.                                                                                                                                                            |
| `patroni_watchdog_enabled`      | no            | Whether to configure the kernel watchdog for additional split brain prevention.                                                                                                                                                                                      |
| `patroni_dcs`                   | etcd          | What backend to use for the DCS. The only option is etcd at the moment.                                                                                                                                                                                              |
| `patroni_listen_port`           | 8008          | REST API TCP port number                                                                                                                                                                                                                                             |
| `patroni_conf_settings`         | {}            | A structured data object with overrides for patroni configuration.<br/>Partial data can be provided and will be merged with the generated config.<br/>Be careful to not override values that are generated based on instance information known at runtime.           |
| `patroni_dynamic_conf_settings` | {}            | Optional structured data just for DCS settings. This will be merged onto `patroni_conf_settings`.                                                                                                                                                                    |
| `patroni_repl_max_lag`          | None          | This is used in the haproxy backend health check only when `haproxy_read_only_load_balancer_enabled` is true.<br/>See [REST API documentation](https://patroni.readthedocs.io/en/latest/rest_api.html#health-check-endpoints) for possible values for `/replica?lag` |

## Patroni configuration file settings

Configuration for patroni is built from three layers, starting with
defaults set by the Patroni daemon, config loaded from the DCS,
and finally from local configuration. The last can be controlled from
either configuration file and overrides via the environment. TPA
controls the configuration file and values are built up in this order.

DCS config to be sent to the API and stored in the bootstrap section
of the config file:

* TPA vars for `postgres` are loaded into the DCS settings,
  see [postgresql.conf.md](postgresql.conf.md).
  Some features are not supported, see notes below.
* Patroni defaults for DCS settings
* User supplied defaults in `patroni_dynamic_conf_settings`, if you want
  to override any DCS settings you can do that here.

Local config stored in the YAML configuration file:

* `bootstrap.dcs` loaded from previous steps above.
* configuration enabled by feature flags, such as `patroni_ssl_enabled`,
  see table above.
* then finally overloaded from user supplied settings, the
  `patroni_conf_settings` option. If you want to change or add
  configuration not controlled by a feature flag then this is the best
  place to do it.

Please note that configuration is *merged* on top of configuration
generated by TPA from cluster information, such as IP addresses,
port numbers, cluster roles, etc. Exercise caution in what you override
as this might affect the stable operation of the cluster.

As Patroni stores all postgres configuration in the DCS and controls
how and when this is distributed to postgres, some features of TPA are
incompatible with patroni:

* It is not possible to change the template
used to generate `postgresql.conf` with the setting
`postgres_conf_template`.
* You cannot change the location of Postgres config files with the
  setting `postgres_conf_dir`.

### Patroni configuration in TPA `config.yml`

You can override single values:

```yaml
cluster_vars:
  patroni_conf_settings:
    bootstrap:
      dcs:
        ttl: 120
```

Or full blocks (with an example from Patroni docs):

```yaml
cluster_vars:
  patroni_conf_settings:
    restapi:
      http_extra_headers:
        'X-Frame-Options': 'SAMEORIGIN'
        'X-XSS-Protection': '1; mode=block'
        'X-Content-Type-Options': 'nosniff'
      https_extra_headers:
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
```

If you want to negate a value or section that is present in the default
TPA config vars you can set the value to `null`. This will cause
patroni to ignore this section when loading the config file.

For example the default TPA config for `log` is

```yaml
log:
  dir: /var/log/patroni
```

To turn off logging add this to `config.yml`:

```yaml
cluster_vars:
  patroni_conf_settings:
    log: null
```

# Patroni cluster management commands

TPA provides these minimal set of tools for managing Patroni
clusters.

## Status

To see the current status of the TPA cluster according to Patroni
run

```shell
tpaexec status cluster_name
```

## Switchover

To perform a switchover to a replica node (e.g. to perform maintenance)
run the command

```shell
tpaexec switchover cluster_name new_primary
```

The new_primary argument must be the name of an existing cluster node
that is currently running as a healthy replica. Checks will be performed
to ensure this is true before a switchover is performed.

Once a switchover has been performed it is recommended that you run
`deploy` and `test` to ensure a healthy cluster.

```shell
tpaexec deploy cluster_name
tpaexec test cluster_name
```

TPA will detect the current role of nodes during deploy regardless of
what config.yml contains, for example if a different node is the leader.
