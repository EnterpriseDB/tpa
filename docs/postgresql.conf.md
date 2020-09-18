# postgresql.conf

TPAexec creates a `conf.d` directory with various `.conf` files under
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

TPAexec splits the configuration up into multiple files. The two main
files are `0000-tpa.conf` and `0001-tpa_restart.conf`. These contain
settings that require a server reload or restart to change,
respectively. During deployment, TPAexec will write any changes to the
correct file and reload or restart Postgres as required.

TPAexec may use other files in certain circumstances (e.g., to configure
optional extensions), but you do not ordinarily need to care where
exactly a given parameter is set.

You should never edit any of the files under `conf.d`, because the
changes may be overwritten when you next run `tpaexec deploy`.

## postgres_conf_settings

TPAexec provides variables like `temp_buffers` and
`maintenance_work_mem` that you can set directly for many, but not all,
available postgresql.conf settings.

You can use `postgres_conf_settings` to set any parameters, whether
recognised by TPAexec or not. You need to quote the value exactly as it
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

This is most useful with settings that TPAexec does not recognise
natively, but you can use it for any parameter (e.g.,
`effective_cache_size` can be set as a variable, but
`authentication_timeout` cannot).

These settings will be written to `conf.d/9900-role-settings.conf`, and
therefore take priority over variables set in any other way.

If you make changes to values under `postgres_conf_settings`, TPAexec
has no way to know whether the a reload is sufficient to effect the
changes, or if a restart is required. Therefore it will always restart
the server to activate the changes. This is why it's always preferable
to use variables directly whenever possible.

## shared_preload_libraries

TPAexec maintains an internal list of extensions that require entries in
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

You could also set `shared_preload_libraries` under
`postgres_conf_settings`, but this should not ordinarily be required,
and should be avoided if possible.

The `shared_preload_libraries` setting lives in
`conf.d/8888-shared_preload_libraries.conf`.

## Making changes by hand

There are two ways you can override anything in the TPAexec-generated
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
deployment if the configuration changes, but TPAexec will never change
`9999-override.conf` after initially creating the empty file.

Depending on which settings you change, you may need to execute
`SELECT pg_reload_conf()` or restart the server for the changes to take
effect.

## Generating postgresql.conf from scratch

By default, TPAexec will leave the default (i.e., `initdb`-generated)
postgresql.conf file alone other than adding the `include_dir`. You
should not ordinarily need to override this behaviour, but you can set
`postgres_conf_template` to do so:

```yaml
cluster_vars:
  postgres_conf_template: 'pgconf.j2'
```

Now the `templates/pgconf.j2` in your cluster directory will be used to
generate postgresql.conf.
