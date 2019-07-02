# BDR-Autoscale

A variant of [BDR-Always-ON](architecture-BDR-Always-ON.md) that
configures BDR autoscaling.

## Cluster configuration

```
[tpa]$ tpaexec configure ~/clusters/bdr-autoscale \
         --architecture BDR-Autoscale \
         --location-names dc-one dc-two \
         --bdr-database bdrdb --bdr-node-group bdrgroup \
         --2Q-repositories products/2ndqpostgres/release products/default/release
```

You must specify ``--architecture BDR-Autoscale``. (In the example
above, this is the only option required to produce a working
configuration.)

You may optionally specify ``--bdr-node-group groupname`` to set the
name of the BDR node group (default: bdrgroup).

You may optionally specify ``--bdr-database dbname`` to set the name of
the database with BDR enabled (default: bdrdb).

You may also specify any of the options described by
[``tpaexec help configure-options``](tpaexec-configure.md).
