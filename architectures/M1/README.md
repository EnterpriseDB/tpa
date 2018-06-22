M1
==

A Postgres cluster with a single primary and n replicas.

Cluster configuration
---------------------

Generate the cluster configuration by running the following command

```
tpaexec configure ~/clusters/m1 --architecture M1 \
  --platform aws --region eu-west-1 --subnet 10.33.115.0/24 \
  --instance-type t2.micro \
  --distribution Debian --minimal
```

You must specify ``--architecture M1``.

You may also specify any of the options described by
``tpaexec help configure-options``.
