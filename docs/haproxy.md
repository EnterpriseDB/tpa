# Configuring haproxy

TPAexec will install and configure haproxy on instances whose `role`
contains `haproxy`.

By default, haproxy listens on `127.0.0.1:5432` for requests forwarded
by [`pgbouncer`](pgbouncer.md) running on the same instance. You must
specify a list of `haproxy_backend_servers` to forward requests to.

You can set the following variables on any `haproxy` instance.

Variable | Default value | Description
---- | ---- | ----
`haproxy_bind_address` | 127.0.0.1 | The address haproxy should bind to
`haproxy_port` | 5432 | The TCP port haproxy should listen on
`haproxy_backend_servers` | None | A list of Postgres instance names
`haproxy_maxconn` | `max_connections`×0.9 | The maximum number of connections allowed per backend server; the default is derived from the backend's `max_connections` setting

## Server options

TPAexec will generate `/etc/haproxy/haproxy.cfg` with a backend that has
a `default-server` line and one line per backend server. All but the
first one will be marked as "backup" servers.

Set `haproxy_default_server_extra_options` to a list of options on the
haproxy instance to add options to the `default-server` line; and set
`haproxy_server_options` to a list of options on the backend server to
add options (which will override the defaults) to the individual server
lines for each backend.

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
