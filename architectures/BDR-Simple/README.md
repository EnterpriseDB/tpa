BDR-Simple
==========

BDR with no frills on N instances, meant primarily for experimentation.
BDR-Always-ON is an alternative that is more geared towards production.

Supports BDRv1, BDRv2, and BDRv3.

Cluster configuration
---------------------

Generate the cluster configuration by running the following command

```
tpaexec configure ~/clusters/bdr --architecture BDR-Simple
```

You must specify ``--architecture BDR-Simple``.

You may specify ``--num-instances 4`` to get a cluster with four
instances. The default is three instances.

You may specify ``--bdr-version <1|2|3>`` to select the desired major
version of BDR (as distinct from ``--bdr-package-version``, see below).

You may specify ``--bdr-node-group groupname`` to set the name of the
BDR node group (default: bdrgroup).

You may specify ``--bdr-database dbname`` to set the name of the
database with BDR enabled (default: bdrdb).

You may also specify any of the options described by
``tpaexec help configure-options``.
