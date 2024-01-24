# Installing haproxy

TPA installs and configures haproxy on instances whose `role`
contains `haproxy`.

By default, haproxy listens on `127.0.0.1:5432` for requests forwarded
by [`pgbouncer`](pgbouncer.md) running on the same instance. You must
specify a list of `haproxy_backend_servers` to forward requests to.

TPA installs the latest available version of haproxy by default.
Set `haproxy_package_version: 1.9.15*` or any valid version specifier 
to install a different version.

!!! Note
    See limitations of using wildcards in `package_version` in
    [tpaexec-configure](tpaexec-configure.md#known-issue-with-wildcard-use).

Haproxy packages are selected according to the type of architecture.
You can use an EDB-managed haproxy package, but it requires a subscription.
Packages from PGDG extras repo can be installed if required.

# Configuring haproxy

You can set the following variables on any `haproxy` instance.

| Variable                  | Default value         | Description                                                                                                                       |
|---------------------------|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| `haproxy_bind_address`    | 127.0.0.1             | The address for haproxy to bind to.                                                                                               |
| `haproxy_port`            | 5432 (5444 for EPAS)  | The TCP port for haproxy to listen on.                                                                                            |
| `haproxy_read_only_port`  | 5433 (5445 for EPAS)  | TCP port for read-only load balancer.                                                                                             |
| `haproxy_backend_servers` | None                  | A list of Postgres instance names.                                                                                                |
| `haproxy_maxconn`         | `max_connections`×0.9 | The maximum number of connections allowed per backend server. The default is derived from the backend's `max_connections` setting. |
| `haproxy_peer_enabled`    | True*                 | Add known haproxy hosts as `peer` list. <br/>*`False` if `failover_manager` is harp or patroni.                                   |

## Read-only load balancer

Haproxy can be configured to listen on an additional port for read-only
access to the database. Currently, this is supported only with the
Patroni failover manager. The backend health check determines which
Postgres instances are currently acting as replicas and uses
round-robin load balancing to distribute traffic to them.

The read-only load balancer is disabled by default. You can turn it on
by setting `haproxy_read_only_load_balancer_enabled: true`.

## Server options

TPA generates `/etc/haproxy/haproxy.cfg` with a backend that has
a `default-server` line and one line per backend server. All but the
first one are marked as "backup" servers.

To add options to the `default-server` line, set `haproxy_default_server_extra_options` to a list of options on the
haproxy instance. 

To add options (which override the defaults) to the individual server
lines for each backend, set
`haproxy_server_options` to a list of options on the backend server.

## Example

```yaml
instances:
- Name: one
  vars:
    haproxy_server_options:
    - maxconn 33
- Name: two
…
- Name: proxy
  role:
  - haproxy
  vars:
    haproxy_backend_servers:
    - one
    - two
    haproxy_default_server_extra_options:
    - on-error mark-down
    - on-marked-down shutdown-sessions
```
