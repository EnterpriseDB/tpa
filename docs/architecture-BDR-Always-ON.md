BDR-Always-ON
=============

This architecture produces a BDRv3 cluster in an Always-ON
configuration, intended for use in production. This is still a work in
progress.

The topology corresponds to v3.1 of the Always-ON architecture.

![BDR-Always-ON cluster](images/bdr-altha31.png)

```
[tpa]$ tpaexec configure ~/clusters/bdr_always_on \
         --architecture BDR-Always-ON
```

This architecture supports all of the additional options described on
the [``tpaexec configure``](tpaexec-configure.md) page.
