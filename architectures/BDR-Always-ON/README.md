BDR-Always-ON
=============

BDR in an Always-ON configuration.

This topology corresponds to v3.1 of the BDR architecture-docs.

Cluster configuration
---------------------

Generate the cluster configuration by running the following command

```
tpaexec configure ~/clusters/bdr --architecture BDR-Always-ON \
  --platform aws --region eu-west-1 --instance-type t3.micro \
  --distribution Debian-minimal
```

You must specify ``--architecture BDR-Always-ON``.

You may specify ``--bdr-node-group groupname`` to set the name of the
BDR node group (default: bdrgroup).

You may specify ``--bdr-database dbname`` to set the name of the
database with BDR enabled (default: bdrdb).

You may also specify any of the options described by
``tpaexec help configure-options``.
