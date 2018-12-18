CAMO2x2
=======

This architecture is based on the
[BDR-Always-ON](BDR-Always-ON.md) architecture. It configures two pairs
of CAMO ("commit at most once") partners in different locations, and
introduces a separate reporting node (a BDR logical standby).

It also allows replication to be configured so as to replicate inserts
and updates between locations, but keep deletes and truncates confined
to the originating pair with the ``--replicate-deletes-locally`` option.

The topology corresponds to v4.0 of the Always-ON architecture.

```
[tpa]$ tpaexec configure ~/clusters/camo2x2 \
         --architecture CAMO2x2 \
         --replicate-deletes-locally \
         --location-names dc-one dc-two \
         --bdr-database bdrdb --bdr-node-group bdrgroup \
         --2Q-repositories products/2ndqpostgres/release products/default/release \
         --extra-postgres-packages postgresql11-zson2q  postgresql11-apptools-zson2q \
         postgresql11-antifreeze
```

(In the above example, only ``--architecture CAMO2x2`` is required to
produce a working configuration.)

This architecture supports all of the additional options described on
the [``tpaexec configure``](tpaexec-configure.md) page.
