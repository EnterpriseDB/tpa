# pg_hba.conf

The Postgres documentation explains the various options available in
[`pg_hba.conf`](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html).

By default, TPAexec will generate a sensible `pg_hba.conf` for your
cluster, to allow replication between instances, and connections from
authenticated clients.

You can add entries to the default configuration by providing a list of
`postgres_hba_settings`:

```yaml
cluster_vars:
  postgres_hba_settings:
  - "# let authenticated users connect from anywhere"
  - hostssl all all 0.0.0.0/0 scram-sha-256
```

You can override the default `local all all peer` line in pg_hba.conf by
setting `postgres_hba_local_auth_method: md5`.

If you don't want any of the default entries, you can change
`postgres_hba_template`:

```yaml
cluster_vars:
  postgres_hba_template: pg_hba.lines.j2
  postgres_hba_settings:
  - "# my lines of text"
  - "# and nothing but my lines"
  - "# …not even any clients!"
  - hostssl all all 0.0.0.0/0 reject
```

You can even create `templates/my_hba.j2` in your cluster directory and
set:

```yaml
cluster_vars:
  postgres_hba_template: my_hba.j2
```

If you just want to leave the existing `pg_hba.conf` alone, you can do
that too:

```yaml
cluster_vars:
  postgres_hba_template: ''
```

Although it is possible to configure `pg_hba.conf` to be different on
different instances, we generally recommend a uniform configuration, so
as to avoid problems with access and replication after any
topology-changing events such as switchovers and failovers.
