CAMO2x2
=======

A variant of BDR-Always-ON with CAMO ("commit at most once") enabled.

This topology corresponds to v4.0 of the TPA Postgres-BDR AlwaysOn
architecture documentation.

Cluster configuration
---------------------

Generate the cluster configuration by running the following command

```
tpaexec configure ~/clusters/bdr --architecture CAMO2x2 \
  --platform aws --region eu-west-1 --instance-type t3.micro \
  --distribution Debian-minimal
```

You must specify ``--architecture CAMO2x2``.

You may optionally specify ``--replicate-deletes-locally`` if you want
the two CAMO partner pairs to be configured to replicate inserts and
updates between all nodes, but to keep deletes and truncates limited
to the originating pair.

You may also specify any of the options described by
``tpaexec help configure-options``.
