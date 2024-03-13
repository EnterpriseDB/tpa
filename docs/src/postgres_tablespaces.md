# Creating Postgres tablespaces

To create Postgres tablespaces during deployment, define their names and
locations in `postgres_tablespaces` under `cluster_vars` or a particular
instance's `vars` in `config.yml`.

If you [define volumes](volumes.md) with
`volume_for: postgres_tablespace` set and a `tablespace_name` defined,
they're added as default entries to `postgres_tablespaces`.

```yaml
cluster_vars:
  postgres_tablespaces:
    explicit:
      location: /some/path

instances:
- Name: example
  …
  volumes:
  - device_name: /dev/xvdh
    …
    vars:
      volume_for: postgres_tablespace
      tablespace_name: implicit
```

This example creates two tablespaces: explicit (at `/some/path`)
and implicit (at `/opt/postgres/tablespaces/implicit/tablespace_data` by
default, unless you specify a different mount point for the volume).

Every `postgres_tablespace` volume must have `tablespace_name` defined.
The tablespace location is derived from the volume's mount point.

Every entry in `postgres_tablespaces` must specify a tablespace name (as
the key) and its `location`. If you're specifying tablespace locations
explicitly, don't put tablespaces inside PGDATA, and don't use any
volume mount point directly as a tablespace location (`lost+found` will
confuse some tools into thinking the directory isn't empty).

By default, the tablespace `owner` is `postgres`, but you can set it to
any valid username. (The users in [`postgres_users`](postgres_users.md)
will have been created by this time.)

Streaming replicas must have the same `postgres_tablespace` volumes and
`postgres_tablespaces` setting as their upstream instance.

You can set the default tablespace for a database in
[`postgres_databases`](postgres_databases.md).
