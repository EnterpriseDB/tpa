# M1

A Postgres cluster with a primary and a streaming replica, one Barman
server, and any number of additional replicas cascaded from the first
one. This architecture is suitable for testing, demonstrating and
learning. We plan to release a production primary/standby architecture
for TPA in the near future.

In default configuration this architecture uses open source software
only. To use subscription-only EDB software with this architecture
requires credentials for EDB Repos 1.0. If you choose EDB Advanced
Server (EPAS) you will also require credentials for the legacy
2ndQuadrant repos.
See [How TPA uses 2ndQuadrant and EDB repositories](2q_and_edb_repositories.md)
for more detail on this topic.

## Default layout

By default, the primary has one read-only replica attached in the same
location; the replica, in turn, has one cascaded replica attached in a
different location, where the Barman server is also configured to take
backups from the primary.

![Cluster with cascading replication](images/m1.png)

If there is an even number of PostgreSQL nodes, the Barman node is
additionally configured as a repmgr witness. This ensures that the
number of repmgr nodes is always odd, which is convenient when
enabling automatic failover.

## Cluster configuration

```
[tpa]$ tpaexec configure ~/clusters/m1 \
         --architecture M1 \
         --platform aws --region eu-west-1 --instance-type t3.micro \
         --distribution Debian-minimal
```

You must specify `--architecture M1`. (In the example above, this is
the only option required to produce a working configuration.)

You may optionally specify `--num-cascaded-replicas N` to request N
cascaded replicas (including 0 for none; default: 1).

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
