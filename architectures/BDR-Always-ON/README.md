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

You may optionally specify ``--region eu-west-1``. This is the default
region, but you may use any existing AWS region that you have access to
(and that will permit the required number of instances to be created).

You may optionally specify ``--subnet 10.33.115.0/24``. This is the
default value, but you SHOULD change it if multiple clusters will be
provisioned at the same time.

You may also specify any of the options described by
``tpaexec help configure-options``.
