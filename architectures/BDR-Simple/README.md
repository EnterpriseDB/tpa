BDR-Simple
==========

BDR with no frills on N instances, meant for experimentation.

Supports both BDRv2 and BDRv3, enable the corresponding product
repository to select between the two.

Cluster configuration
---------------------

Generate the cluster configuration by running the following command

```
tpaexec configure ~/clusters/bdr --architecture BDR-Simple
```

You must specify ``--architecture BDR-Simple``.

You may specify ``--num-instances 4`` to get a cluster with four
instances. The default is three instances.

You may also specify any of the options described by
``tpaexec help configure-options``.
