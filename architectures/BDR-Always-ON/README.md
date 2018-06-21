BDR-Always-ON
=============

BDR in an Always-ON configuration.

Cluster configuration
---------------------

Generate the cluster configuration by running the following command

```
tpaexec configure ~/clusters/bdr --architecture BDR-Always-ON \
  --platform aws --region eu-west-1 --subnet 10.33.115.0/24 \
  --instance-type t2.micro \
  --distribution Debian --minimal
```

You must specify ``--architecture BDR-Always-ON``.

You may also specify any of the options described by
``tpaexec help configure-options``.
