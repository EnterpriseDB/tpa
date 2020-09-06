# Running initdb

TPAexec will first create `postgres_data_dir` if it does not exist, and
ensure it has the correct ownership, permissions, and SELinux context.
Then, unless the directory already contains a `VERSION` file, it will
run `initdb` to initialise `postgres_data_dir`.

You can use the
[pre-initdb hook](tpaexec-hooks.md#pre-initdb)
to execute tasks before `postgres_data_dir` is created and `initdb` is
run. If the hook initialises `postgres_data_dir`, TPAexec will find the
`VERSION` file and realise that it does not need to run `initdb` itself.

You can optionally set `postgres_initdb_opts` to a list of options to
pass to `initdb`:

```yaml
cluster_vars:
  postgres_locale: de_DE.UTF-8
  postgres_initdb_opts:
  - --data-checksums
```

We recommend always including the `--data-checksums` option (which is
included by default).

TPAexec will set `TZ=UTC` in the environment, and set `LC_ALL` to
the `postgres_locale` you specify, when running `initdb`.

## Separate configuration directory

By default, `postgres_conf_dir` is equal to `postgres_data_dir`, and the
Postgres configuration files (postgresql.conf, pg_ident.conf,
pg_hba.conf, and the include files in conf.d) are created within the
data directory. If you change `postgres_conf_dir`, TPAexec will move the
generated configuration files to the new location after running
`initdb`.
