---
description: Perform a controlled switchover between a primary and a replica in a cluster that uses streaming replication.
---

# tpaexec switchover

The `tpaexec switchover` command performs a controlled switchover
between a primary and a replica in a [cluster that uses streaming
replication](architecture-M1.md). After you run this command, the
selected replica is promoted to be the new primary, the former primary
becomes a new replica, and any other replicas in the cluster will be
reconfigured to follow the new primary.

The command checks that the cluster is healthy before switching roles,
and is designed to be run without having to shut down any repmgr
services beforehand.

(This is equivalent to running `repmgr standby switchover` with the
`--siblings-follow` option.)

## Example

This command will make `replicaname` be the new primary in
`~/clusters/speedy`:

```bash
tpaexec switchover ~/clusters/speedy replicaname
```

## Architecture options

This command is applicable only to [M1 clusters](architecture-M1.md)
that have a single writable primary instance and one or more read-only
replicas.

For BDR-Always-ON clusters, use the
[HAProxy server pool management commands](tpaexec-server-pool.md) to
perform maintenance on PGD instances.

## Repmgr redirect pgbouncer

When using repmgr as failover manager, pgbouncer as connection pooler and
setting `repmgr_redirect_pgbouncer: true`, switchover command ensures that
the pgbouncer instances are redirected to the new primary node.

!!! Note Revert to initial primary
    In case you already switched over to a different primary, you can specify `revert_redirect: true`
    on the command that will switch back to the initial primary to make use of the initial pgbouncer config file instead of regenerating it.
    TPA saves the initial state of this config file as `pgbouncer.databases.ini.orig` during a switchover and can revert to it when going back to the initial primary

    ```bash
        # switchover to a replica
        tpaexec switchover <cluster_name> <replica_name>
        # revert to initial primary
        tpaexec switchover <cluster_name> <initial_primary_name> -e"revert_redirect=true"
