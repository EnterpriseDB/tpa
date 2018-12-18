CAMO2x2
=======

A variant of [BDR-Always-ON](architecture-BDR-Always-ON.md) that
configures two pairs of CAMO ("commit at most once") partners in
different locations and adds a separate BDR logical standby as a
reporting node.

It also allows replication to be configured so as to replicate inserts
and updates between locations, but keep deletes and truncates confined
to the originating pair.

The topology corresponds to v4.0 of the Always-ON architecture.

## Cluster configuration

```
[tpa]$ tpaexec configure ~/clusters/camo2x2 \
         --architecture CAMO2x2 \
         --replicate-deletes-locally \
         --location-names dc-one dc-two \
         --bdr-database bdrdb --bdr-node-group bdrgroup \
         --2Q-repositories products/2ndqpostgres/release products/default/release \
         --extra-postgres-packages postgresql11-zson2q postgresql11-apptools-zson2q \
         postgresql11-antifreeze
```

You must specify ``--architecture CAMO2x2``. (In the example above, this
is the only option required to produce a working configuration.)

You may optionally specify ``--replicate-deletes-locally`` if you do not
want deletes and truncates replicated between locations.

You may optionally specify ``--bdr-node-group groupname`` to set the
name of the BDR node group (default: bdrgroup).

You may optionally specify ``--bdr-database dbname`` to set the name of
the database with BDR enabled (default: bdrdb).

You may also specify any of the options described by
[``tpaexec help configure-options``](tpaexec-configure.md).
