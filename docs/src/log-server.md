---
description: Centralizing cluster logs with TPA's `log-server` role.
---

# Log server

Assigning the `log-server` role to one instance in config.yml turns it
into a central rsyslog destination for the cluster. TPA then
automatically configures every other instance to forward its logs
there — no further configuration is needed. Assign the role to only
one instance per cluster: TPA won't stop you from adding it to more
than one, but only the first one found is actually used, so any others
just sit idle.

Centralizing logs this way means you don't have to log into each
instance separately to piece together what happened during a
cluster-wide event, such as a failover. It also gives you a copy of an
instance's logs that survives that instance being replaced or torn
down, and a single place to point log rotation, monitoring, or
shipping tools at instead of configuring them on every instance.

```yaml
instances:
- Name: uproar
  role:
  - primary

- Name: kinsman
  role:
  - barman
  - log-server
  - witness
```

## What TPA configures

On every instance other than the log server, TPA forwards the
following programs' log output to it over TCP port 601:

- `postgres`
- `pgbouncer`
- `repmgrd`
- `harp-manager`
- `harp-proxy`
- `barman`
- `efm`

If the log server is temporarily unreachable, messages are queued to
local disk (up to 1 GB) and delivery is retried indefinitely once it
comes back.

On the log server instance itself, TPA:

- Enables TCP syslog reception on port 601, and UDP reception on port
  514 as well when `failover_manager` is set to `efm` (EFM ships its
  logs over UDP).
- Creates `/var/log/hosts/` and writes each sending host's messages
  there, one file per host and program:
  `/var/log/hosts/<hostname>/<programname>.log-YYYYMMDD`.
- If the log server instance also has the `barman` role, tails its own
  `/var/log/barman/barman.log` into the same pipeline.

## Effect on individual components

Whether `log_server` is set for an instance changes how some
components log on it:

- **Postgres** keeps writing to its local log file regardless; when
  `log_server` is set, its output is additionally forwarded to the log
  server.
- **pgbouncer** logs via syslog (`syslog_facility = daemon`,
  `syslog_ident = pgbouncer`) instead of to
  `/var/log/pgbouncer/pgbouncer.log`.
- **EFM** has `syslog.enabled` set to `true` and `syslog.host` set to
  the instance's own hostname, so it logs through the local syslog
  daemon, which then forwards the messages on.

## Overriding the default log server

If no instance has the `log-server` role, `log_server` is never set
and every instance just logs locally. Once one instance has the role,
every other instance defaults to sending its logs there. To route a
specific instance's logs elsewhere instead, set `log_server` under
that instance's `vars`:

```yaml
- Name: unravel
  role:
  - replica
  vars:
    log_server: some-other-host
```
