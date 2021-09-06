# Configuring pgbouncer

TPAexec will install and configure pgbouncer on instances whose `role`
contains `pgbouncer`.

By default, pgbouncer listens for connections on port 6432 and forwards
connections to `127.0.0.1:5432` (which may be either Postgres or
[haproxy](haproxy.md), depending on the architecture).

You can set the following variables on any `pgbouncer` instance.

Variable | Default value | Description
---- | ---- | ----
`pgbouncer_port` | 6432 | The TCP port pgbouncer should listen on
`pgbouncer_backend` | 127.0.0.1 | A Postgres server to connect to
`pgbouncer_backend_port` | 5432 | The port that the `pgbouncer_backend` listens on
`pgbouncer_max_client_conn` | `max_connections`×0.9 | The maximum number of connections allowed; the default is derived from the backend's `max_connections` setting if possible
`pgbouncer_auth_user` | pgbouncer_auth_user | Postgres user to use for authentication

## Databases

By default, TPAexec will generate
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
