# Using Patroni as a failover manager

You can use Patroni as a single-master failover manager with the M1
architecture using the following command options:

```shell
tpaexec configure cluster_name -a M1 --enable-patroni --postgresql 14
```

You can also use Patroni as a failover manager by setting the following
`config.yml` option:

```yaml
cluster_vars:
  failover_manager: patroni
```

If deploying to RedHat, you must also add the `PGDG` repository to your
yum repository list in `config.yml`:

```yaml
cluster_vars:
  yum_repository_list:
  - PGDG
```

TPA `configure` adds 3 etcd nodes and 2 haproxy nodes. Etcd is used
for the Distributed Configuration Store (DCS). Patroni supports other
DCS backends, but they aren't currently supported by EDB or TPA.

TPA uses Patroni's feature of converting an existing PostgreSQL
standalone server. This mechanism allows for TPA to initialize and manage
configuration. Once a single PostgreSQL server and database is
created, Patroni creates replicas and configures replication.
TPA then removes any Postgres configuration files used during setup.

Once this is set up, you can continue to manage Postgres using TPA and settings
in `config.yml` for the cluster. You can also use Patroni interfaces,
such as the command line `patronictl` and the REST API, but we
recommend using TPA methods wherever possible.

# Configuration options

You can use these configuration variables to control certain behaviors
when deploying Patroni in TPA.

| Variable                        | Default value | Description                                                                                                                                                                                                                                                          |
|---------------------------------|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `patroni_super_user`            | postgres      | User to create in Postgres for superuser role.                                                                                                                                                                                                                       |
| `patroni_replication_user`      | replicator    | Username to create in Postgres for replication role.                                                                                                                                                                                                                 |
| `patroni_restapi_user`          | patroni       | Username to configure for the Patroni REST API.                                                                                                                                                                                                                      |
| `patroni_rewind_user`           | rewind        | Username to create in postgres for pg_rewind function.                                                                                                                                                                                                               |
| `patroni_installation_method`   | pkg           | Install Patroni from packages or source (for example, Git repo or local source directory if Docker).                                                                                                                                                                         |
| `patroni_ssl_enabled`           | no            | Whether to enable SSL for REST API and ctl connection. Uses the cluster SSL cert and CA if available.                                                                                                                                                            |
| `patroni_rewind_enabled`        | yes           | Whether to enable Postgres rewind; creates a user defined by patroni_rewind_user and adds config section.                                                                                                                                                            |
| `patroni_watchdog_enabled`      | no            | Whether to configure the kernel watchdog for additional split-brain prevention.                                                                                                                                                                                      |
| `patroni_dcs`                   | etcd          | The backend to use for the DCS. Currently, the only option is etcd.                                                                                                                                                                                              |
| `patroni_listen_port`           | 8008          | REST API TCP port number.                                                                                                                                                                                                                                             |
| `patroni_conf_settings`         | {}            | A structured data object with overrides for Patroni configuration.<br/>Partial data can be provided and will be merged with the generated config.<br/>Be careful to not override values that are generated based on instance information known at runtime.           |
| `patroni_dynamic_conf_settings` | {}            | Optional structured data just for DCS settings. This will be merged onto `patroni_conf_settings`.                                                                                                                                                                    |
| `patroni_repl_max_lag`          | None          | This is used in the haproxy backend health check only when `haproxy_read_only_load_balancer_enabled` is true.<br/>See [REST API documentation](https://patroni.readthedocs.io/en/latest/rest_api.html#health-check-endpoints) for possible values for `/replica?lag`. |

## Patroni configuration file settings

Configuration for Patroni is built from three layers, starting with
defaults set by the Patroni daemon, config loaded from the DCS,
and finally from local configuration. The last can be controlled from
either configuration file and overrides by way of the environment. TPA
controls the configuration file, and values are built up in this order.

DCS config to be sent to the API and stored in the bootstrap section
of the config file:

* TPA vars for `postgres` are loaded into the DCS settings.
  See [postgresql.conf.md](postgresql.conf.md).
  Some features aren't supported. See notes that follow.
* Patroni defaults for DCS settings.
* User-supplied defaults in `patroni_dynamic_conf_settings`. If you want
  to override any DCS settings, you can do that here.

Local config stored in the YAML configuration file:

* `bootstrap.dcs` loaded from previous steps.
* Configuration enabled by feature flags, such as `patroni_ssl_enabled`.
  See the table in [Configuration options](#configuration-options).
* Then, finally, overloaded from user-supplied settings, the
  `patroni_conf_settings` option. If you want to change or add
  a configuration not controlled by a feature flag, then this is the best
  place to do it.

Configuration is merged on top of the configuration
generated by TPA from cluster information, such as IP addresses,
port numbers, cluster roles, and so on. Use caution in what you override,
as this might affect the stable operation of the cluster.

As Patroni stores all Postgres configuration in the DCS and controls
how and when this is distributed to Postgres, some features of TPA are
incompatible with Patroni:

* You can't change the template
used to generate `postgresql.conf` with the setting
`postgres_conf_template`.
* You can't change the location of Postgres config files with the
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

You can also override full blocks (with an example from Patroni documentation):

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

If you want to negate a value or section that's present in the default
TPA config vars, you can set the value to `null`. This causes
Patroni to ignore this section when loading the config file.

For example, the default TPA config for `log` is:

```yaml
log:
  dir: /var/log/patroni
```

To turn off logging, add this to `config.yml`:

```yaml
cluster_vars:
  patroni_conf_settings:
    log: null
```

# Patroni cluster management commands

TPA provides this minimal set of tools for managing Patroni
clusters.

## Status

To see the current status of the TPA cluster according to Patroni,
run:

```shell
tpaexec status cluster_name
```

## Switchover

To perform a switchover to a replica node (for example, to perform maintenance)
run:

```shell
tpaexec switchover cluster_name <new_primary>
```

The `new_primary` argument must be the name of an existing cluster node
that's currently running as a healthy replica. Checks are performed
to ensure this is true before a switchover is performed.

Once a switchover has been performed, we recommend that you run
`deploy` and `test` to ensure a healthy cluster:

```shell
tpaexec deploy cluster_name
tpaexec test cluster_name
```

TPA detects the current role of nodes during deploy regardless of
what `config.yml` contains, for example, if a different node is the leader.
