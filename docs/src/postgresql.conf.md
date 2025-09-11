---
description: Modifying postgresql.conf on a TPA-managed Postgres cluster.
---


# postgresql.conf

TPA creates a `conf.d` directory with various `.conf` files under
it, and uses `include_dir` in the main `postgresql.conf` to use these
additional configuration files.

The Postgres configuration files (postgresql.conf, pg_ident.conf, and
pg_hba.conf) and the included files under `conf.d` are always stored in
`postgres_conf_dir`. This is the same as `postgres_data_dir` by default,
but you can set it to a different location if you wish to keep the
configuration separate from the data directory.

The main configuration mechanism is to set variables directly:

```yaml
cluster_vars:
  temp_buffers: 16MB
  log_connections: on
  autovacuum_vacuum_cost_limit: -1
  effective_cache_size: 4GB
  max_connections: 300
  max_wal_senders: 32
```

TPA splits the configuration up into multiple files. The two main
files are `0000-tpa.conf` and `0001-tpa_restart.conf`. These contain
settings that require a server reload or restart to change,
respectively. During deployment, TPA will write any changes to the
correct file and reload or restart Postgres as required.

TPA may use other files in certain circumstances (e.g., to configure
optional extensions), but you do not ordinarily need to care where
exactly a given parameter is set.

You should never edit any of the files under `conf.d`, because the
changes may be overwritten when you next run `tpaexec deploy`.

## postgres_conf_settings

TPA provides variables like `temp_buffers` and
`maintenance_work_mem` that you can set directly for many, but not all,
available postgresql.conf settings.

You can use `postgres_conf_settings` to set any parameters, whether
recognised by TPA or not. You need to quote the value exactly as it
would appear in `postgresql.conf`:

```yaml
cluster_vars:
  effective_cache_size: 2GB
  postgres_conf_settings:
    effective_cache_size: 4GB
    authentication_timeout: 1min
    synchronous_standby_names: >-
      'any 2 ("first", "second", "third")'
    bdr.global_lock_statement_timeout: 60s
```

This is most useful with settings that TPA does not recognise
natively, but you can use it for any parameter (e.g.,
`effective_cache_size` can be set as a variable, but
`authentication_timeout` cannot).

These settings will be written to `conf.d/9900-role-settings.conf`, and
therefore take priority over variables set in any other way.

If you make changes to values under `postgres_conf_settings`, TPA
has no way to know whether the a reload is sufficient to effect the
changes, or if a restart is required. Therefore it will always restart
the server to activate the changes. This is why it's always preferable
to use variables directly whenever possible.

## shared_buffers

By default, TPA will set `shared_buffers` to 25% of the available memory
(this is just a rule of thumb, not a recommendation). You can override this
default by setting `shared_buffers_ratio: 0.35` to use a different proportion,
or by setting `shared_buffers_mb: 796` to a specific number of MB, or by
specifying an exact value directly, e.g., `shared_buffers: "2GB"`.

## effective_cache_size

By default, TPA will set `effective_cache_size` to 50% of the available
memory. You can override this default by setting
`effective_cache_size_ratio: 0.35` to use a different proportion, or by setting
`effective_cache_size_mb: 796` to a specific number of MB, or by specifying an
exact value directly, e.g., `effective_cache_size: "8GB"`.

## shared_preload_libraries

TPA maintains an internal list of extensions that require entries in
`shared_preload_libraries` to work, and if you include any such
extensions in `postgres_extensions`, it will automatically update
`shared_preload_libraries` for you.

If you are using unrecognised extensions that require preloading, you
can add them to `preload_extensions`:

```yaml
cluster_vars:
  preload_extensions:
  - myext
  - otherext
```

Now if you add `myext` to `postgres_extensions`,
`shared_preload_libraries` will include `myext`.

By default, `shared_preload_libraries` is set in
`conf.d/8888-shared_preload_libraries.conf`.

Setting `shared_preload_libraries` directly as a variable is not
supported. You should not normally need to set it, but if unavoidable,
you can set a fully-quoted value under
[`postgres_conf_settings`](#postgres_conf_settings). In this case, the
value is set in `conf.d/9900-tpa_postgres_conf_settings.conf`.

## Postgres log

The default log file is defined as `/var/log/postgres/postgres.log`. If you
need to change that, you can now set postgres_log_file in your config.yml:

```yaml
cluster_vars:
  [...]
  postgres_log_file: '/srv/fantastic_logs/pg_server.log'
```

TPA will take care of creating the directories and rotate the log when needed.

## SSL configuration

By default, TPA will generate a private key and a self-signed TLS
certificate which are used by Postgres as the `ssl_key_file` and
`ssl_cert_file` respectively. The files are named using the TPA cluster
name (`cluster_name.key` and `cluster_name.crt`) and located in
`/etc/tpa`, resulting in the following default configuration in 
`0001-tpa_restart.conf`:

```ini
ssl_key_file=/etc/tpa/cluster_name.key
ssl_cert_file=/etc/tpa/cluster_name.crt
```

This is sufficient to ensure
that traffic between clients and server is encrypted in transit. 

To provide your own certificates, upload them to the target nodes as
[artifacts](artifacts.md), then set the path by specifying the following
cluster variables:

```yaml
cluster_vars:
  ...
  artifacts:
  - type: file
    dest: /path/to/your_key.key
    src: /local/path/to/your_key.key
    owner: root
    group: root
    mode: "0644"
  - type: file
    dest: /path/to/your_cert.crt
    src: /local/path/to/your_cert.crt
    owner: root
    group: root
    mode: "0600"
  ssl_key_file: /path/to/your_key.key
  ssl_cert_file: /path/to/your_cert.crt
```

Alternatively, if you upload your key and certificate to the default
location, TPA will use them instead of generating its own, and you do
not need to specify `ssl_key_file` or `ssl_cert_file`. Note, however,
that you must explicitly create `/etc/tpa` because it doesn't exist at
the time artifacts are uploaded. The permissions and ownership of these
files will be adjusted by TPA when the `postgres` user is created during
deployment.

```yaml
cluster_vars:
  ...
  artifacts:
  - type: path
    path: /etc/tpa
    state: directory
    owner: root
    group: root
    mode: "0755"
  - type: file
    dest: /etc/tpa/cluster_name.key
    src: /local/path/to/your_key.key
    owner: root
    group: root
    mode: "0644"
  - type: file
    dest: /etc/tpa/cluster_name.crt
    src: /local/path/to/your_cert.crt
    owner: root
    group: root
    mode: "0600"
```

!!!Note Other SSL settings 
TPA does not specify `ssl_ca_file` or `ssl_crl_file` by default. To
provide these files yourself you can do so using
[artifacts](artifacts.md) and by specifying the cluster variables of the
same name. 
!!!

## Making changes by hand

There are two ways you can override anything in the TPA-generated
configuration.

The first (and recommended) option is to use `ALTER SYSTEM`, which
always takes precedence over anything in the configuration files:

```sql
# ALTER SYSTEM SET bdr.global_lock_statement_timeout TO '60s';
```

You can also edit `conf.d/9999-override.conf`:

```bash
$ echo "bdr.global_lock_statement_timeout='60s'" >> conf.d/9999-override.conf
```

All other files under `conf.d` are subject to be overwritten during
deployment if the configuration changes, but TPA will never change
`9999-override.conf` after initially creating the empty file.

Depending on which settings you change, you may need to execute
`SELECT pg_reload_conf()` or restart the server for the changes to take
effect.

## Generating postgresql.conf from scratch

By default, TPA will leave the default (i.e., `initdb`-generated)
postgresql.conf file alone other than adding the `include_dir`. You
should not ordinarily need to override this behaviour, but you can set
`postgres_conf_template` to do so:

```yaml
cluster_vars:
  postgres_conf_template: 'pgconf.j2'
```

Now the `templates/pgconf.j2` in your cluster directory will be used to
generate postgresql.conf.
