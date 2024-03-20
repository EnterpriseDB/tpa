# postgresql.conf

TPA creates a `conf.d` directory with various `.conf` files under
it. It uses `include_dir` in the main `postgresql.conf` to use these
additional configuration files.

The Postgres configuration files (`postgresql.conf`, `pg_ident.conf`, and
p`g_hba.conf`) and the included files under `conf.d` are always stored in
`postgres_conf_dir`. This location is the same as `postgres_data_dir` by default,
but you can set it to a different location if you want to keep the
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

TPA splits the configuration into multiple files. The two main
files are `0000-tpa.conf` and `0001-tpa_restart.conf`. These contain
settings that require a server reload (for `0000-tpa.conf`) 
or restart (for `0001-tpa_restart.conf`) to change.
During deployment, TPA writes any changes to the
correct file and reloads or restarts Postgres as required.

TPA might use other files in certain circumstances (for example, to configure
optional extensions), but you don't ordinarily need to know where
exactly a given parameter is set.

Never edit any of the files under `conf.d`. The
changes might be overwritten when you next run `tpaexec deploy`.

## postgres_conf_settings

TPA provides variables like `temp_buffers` and
`maintenance_work_mem` that you can set directly for many, but not all,
available `postgresql.conf` settings.

You can use `postgres_conf_settings` to set any parameters, whether
recognized by TPA or not. You need to quote the value exactly as it
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

This approach is most useful with settings that TPA doesn't recognize
natively, but you can use it for any parameter. For example, 
`effective_cache_size` can be set as a variable, but 
`authentication_timeout` can't be.

These settings are written to `conf.d/9900-role-settings.conf` and
therefore take priority over variables set in any other way.

If you make changes to values under `postgres_conf_settings`, TPA
doesn't know whether a reload is sufficient to activate the
changes or if a restart is required. Therefore, it always restarts
the server to activate the changes. For this reason, it's always preferable
to use variables directly whenever possible.

## shared_buffers

By default, TPA sets `shared_buffers` to 25% of the available memory
(this is just a general estimate, not a recommendation). You can override this
default by either:

-  Setting `shared_buffers_ratio: 0.35` to use a different proportion
-  Setting `shared_buffers_mb: 796` to a specific number of MB
-  Specifying an exact value directly, for example, `shared_buffers: "2GB"`

## effective_cache_size

By default, TPA sets `effective_cache_size` to 50% of the available
memory. You can override this default by either:

- Setting `effective_cache_size_ratio: 0.35` to use a different proportion 
- Setting `effective_cache_size_mb: 796` to a specific number of MB 
- Specifying an exact value directly, for example, `effective_cache_size: "8GB"`

## shared_preload_libraries

TPA maintains an internal list of extensions that require entries in
`shared_preload_libraries` to work. If you include any such
extensions in `postgres_extensions`, TPA updates
`shared_preload_libraries` for you.

If you're using unrecognized extensions that require preloading, you
can add them to `preload_extensions`:

```yaml
cluster_vars:
  preload_extensions:
  - myext
  - otherext
```

With this setting in place, if you add `myext` to `postgres_extensions`,
`shared_preload_libraries` will include `myext`.

By default, `shared_preload_libraries` is set in
`conf.d/8888-shared_preload_libraries.conf`.

Setting `shared_preload_libraries` directly as a variable isn't
supported. You don't normally need to set it, but if doing so is unavoidable,
you can set a fully quoted value under
[`postgres_conf_settings`](#postgres_conf_settings). In this case, the
value is set in `conf.d/9900-tpa_postgres_conf_settings.conf`.

## Postgres log

The default log file is defined as `/var/log/postgres/postgres.log`. If you
need to change that, you can now set `postgres_log_file` in your `config.yml`:

```yaml
cluster_vars:
  [...]
  postgres_log_file: '/srv/fantastic_logs/pg_server.log'
```

TPA creates the directories and rotates the log when needed.

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
deployment if the configuration changes. But TPA will never change
`9999-override.conf` after initially creating the empty file.

Depending on the settings you change, you might need to execute
`SELECT pg_reload_conf()` or restart the server for the changes to take
effect.

## Generating postgresql.conf from scratch

By default, TPA leaves the default (that is, `initdb`-generated)
`postgresql.conf` file alone other than adding the `include_dir`. You
don't ordinarily need to override this behavior, but you can set
`postgres_conf_template` to do so:

```yaml
cluster_vars:
  postgres_conf_template: 'pgconf.j2'
```

With this setting in place, `templates/pgconf.j2` in your cluster directory is used to
generate `postgresql.conf`.
