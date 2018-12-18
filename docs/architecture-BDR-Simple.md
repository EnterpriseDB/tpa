BDR-Simple
==========

This architecture produces a no-frills BDR cluster with N instances (in
a mesh topology). It is meant primarily for experimentation with BDR.

It supports BDRv1 (with BDR-Postgres 9.4),
BDRv2 (with Postgres 9.6 or 2ndQPostgres 9.6), and
BDRv3 (with Postgres or 2ndQPostgres 10 and above).

If you are using BDRv2 or BDRv3 or 2ndQPostgres, you must have access to
the corresponding product repository through the 2ndQuadrant portal.

By default, the cluster will have two instances running Postgres 10 and
BDRv3.

Use ``--num-instances N`` to change the number of instances.

Use ``--postgres-version X`` or ``--bdr-version Y`` to select the
Postgres or BDR version.

Use ``--2Q-repositories products/bdr2/snapshot`` for snapshot packages
of BDRv2 instead of the default release packages, or
``products/bdr3/snapshot products/pglogical3/snapshot`` for snapshot
packages of BDRv3. Add ``products/2ndqpostgres/release`` to the list
to use 2ndQPostgres release packages.

BDRv1 supports only BDR-Postgres 9.4, BDRv2 supports only Postgres 9.6,
and BDRv3 supports only Postgres 10 and above. If you specify only the
desired major version, the correct version of BDR will be selected by
default. If you specify only the desired BDR version, the correct major
version of Postgres will be selected by default.

![BDR-Simple cluster](images/bdr-simple.png)

```
[tpa]$ tpaexec configure ~/clusters/bdr_simple \
         --architecture BDR-Simple --num-instances 3 \
         --bdr-version 2
```

This architecture supports all of the additional options described on
the [``tpaexec configure``](tpaexec-configure.md) page.
