# Running initdb

TPA first creates `postgres_data_dir` if it doesn't exist and
ensures it has the correct ownership, permissions, and SELinux context.
Then, unless the directory already contains a `VERSION` file, it
runs `initdb` to initialize `postgres_data_dir`.

You can use the
[pre-initdb hook](tpaexec-hooks.md#pre-initdb)
to execute tasks before `postgres_data_dir` is created and `initdb` is
run. If the hook initializes `postgres_data_dir`, TPA finds the
`VERSION` file and therefore doesn't run `initdb`.

You can optionally set `postgres_initdb_opts` to a list of options to
pass to `initdb`:

```yaml
cluster_vars:
  postgres_locale: de_DE.UTF-8
  postgres_initdb_opts:
  - --data-checksums
```

We recommend always including the `--data-checksums` option, which is
included by default.

When running `initdb`, TPA sets `TZ=UTC` in the environment and sets `LC_ALL` to
the `postgres_locale` you specify.

## Separate configuration directory

By default, `postgres_conf_dir` is equal to `postgres_data_dir`, and the
Postgres configuration files (`postgresql.conf`, `pg_ident.conf`,
`pg_hba.conf`, and the include files in `conf.d`) are created in the
data directory. If you change `postgres_conf_dir`, after running
`initdb`, TPA moves the
generated configuration files to the new location.
