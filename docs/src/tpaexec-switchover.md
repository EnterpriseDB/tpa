# tpaexec switchover

The `tpaexec switchover` command performs a controlled switchover
between a primary and a replica in a [cluster that uses streaming
replication](architecture-M1.md). After you run this command, the
selected replica is promoted to be the new primary, the former primary
becomes a new replica, and any other replicas in the cluster will be
reconfigured to follow the new primary.

The command performs various sanity checks before switching roles, and
is designed to be run without having to shut down any repmgr services
beforehand.

(This is equivalent to running `repmgr standby switchover` with the
`--siblings-follow` option.)

## Example

This command will make `replicaname` be the new primary in
`~/clusters/speedy`:

```bash
$ tpaexec switchover ~/clusters/speedy replicaname
```

## Architecture options

This command is applicable only to [M1 clusters](architecture-M1.md)
that have a single writable primary instance and one or more read-only
replicas.

For BDR-Always-ON clusters, use the
[HAProxy server pool management commands](tpaexec-server-pool.md) to
perform maintenance on BDR instances.
