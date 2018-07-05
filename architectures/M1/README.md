M1
==

A Postgres cluster with a single primary and n replicas.

Cluster configuration
---------------------

Generate the cluster configuration by running the following command

```
tpaexec configure ~/clusters/m1 --architecture M1 \
  --platform aws --region eu-west-1 --instance-type t2.micro \
  --distribution Debian --minimal
```

You must specify ``--architecture M1``.

By default, the primary has one streaming replica attached to it, and
the replica itself has one cascaded replica attached. You may optionally
specify ``--num-cascaded-replicas 3`` to increase the number of cascaded
replicas (or specify 0 to have none).

You may also specify any of the options described by
``tpaexec help configure-options``.
