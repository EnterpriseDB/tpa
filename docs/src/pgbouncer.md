---
description: Adding PgBouncer to your Postgres cluster.
---

# PgBouncer

## PgBouncer package version

By default, TPA installs the latest available version of PgBouncer.

The version of the PgBouncer package that is installed can be specified 
by including `pgbouncer_package_version: xxx` under the `cluster_vars` 
section of the `config.yml` file.

```yaml
cluster_vars:
    …
    pgbouncer_package_version: '1.8*'
    …
```

You may use any version specifier that apt or yum would accept.

If your version does not match, try appending a `*` wildcard. This
is often necessary when the package version has an epoch qualifier
like `2:...`.


## Configuring PgBouncer

TPA will install and configure PgBouncer on instances whose `role`
contains `pgbouncer`.

By default, PgBouncer listens for connections on port 6432 and, if no
`pgbouncer_backend` is specified, forwards connections to
`127.0.0.1:5432` (which may be either Postgres or [haproxy](haproxy.md),
depending on the architecture).

!!! Note Using PgBouncer to route traffic to the primary
If you are using the M1 architecture with repmgr you can set
`repmgr_redirect_pgbouncer: true` hash under `cluster_vars` to have
PgBouncer connections directed to the primary. The PgBouncer will be
automatically updated on failover to route to the new primary. You
should use this option in combination with setting `pgbouncer_backend`
to the primary instance name to ensure that the cluster is initially
deployed with PgBouncer configured to route to the primary.
!!!

You can set the following variables on any `pgbouncer` instance.

Variable | Default value | Description
---- | ---- | ----
`pgbouncer_port` | 6432 | The TCP port pgbouncer should listen on
`pgbouncer_backend` | 127.0.0.1 | A Postgres server to connect to
`pgbouncer_backend_port` | 5432 | The port that the `pgbouncer_backend` listens on
`pgbouncer_max_client_conn` | `max_connections`×0.9 | The maximum number of connections allowed; the default is derived from the backend's `max_connections` setting if possible
`pgbouncer_auth_user` | pgbouncer_auth_user | Postgres user to use for authentication

## Databases

By default, TPA will generate
`/etc/pgbouncer/pgbouncer.databases.ini` with a single wildcard `*`
entry under `[databases]` to forward all connections to the backend
server. You can set `pgbouncer_databases` as shown in the example below
to change the database configuration.

## Authentication

PgBouncer will connect to Postgres as the `pgbouncer_auth_user` and
execute the (already configured) `auth_query` to authenticate users.

## Example

```yaml
instances:
- Name: one
  vars:
    max_connections: 300
- Name: two
- Name: proxy
  role:
  - pgbouncer
  vars:
    pgbouncer_backend: one
    pgbouncer_databases:
    - name: dbname
      options:
        pool_mode: transaction
        dbname: otherdb
    - name: bdrdb
      options:
        host: two
        port: 6543
```
