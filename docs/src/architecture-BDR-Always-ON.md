# BDR-Always-ON

EDB Postgres Distributed 4 or below in an Always-ON configuration,
suitable for use in test and production.

This architecture requires a subscription to the legacy 2ndQuadrant
repositories, and some options require a subscription to EDB Repos 1.0.
See [How TPA uses 2ndQuadrant and EDB repositories](2q_and_edb_repositories.md)
for more detail on this topic.

The BDR-Always-ON architecture has four variants, which can be
selected with the `--layout` configure option:

1. bronze: 2×bdr+primary, bdr+witness, barman, 2×harp-proxy

2. silver: bronze, with bdr+witness promoted to bdr+primary, and barman
moved to separate location

3. gold: two symmetric locations with 2×bdr+primary, 2×harp-proxy,
and barman each; plus a bdr+witness in a third location

4. platinum: gold, but with one bdr+readonly (logical standby) added to
each of the main locations

You can check EDB's Postgres-BDR Always On Architectures
[whitepaper](https://www.enterprisedb.com/promote/bdr-always-on-architectures)
for the detailed layout diagrams.

This architecture is meant for use with BDR versions 3.6, 3.7, and 4.

## Cluster configuration

```
[tpa]$ tpaexec configure ~/clusters/bdr \
         --architecture BDR-Always-ON \
         --layout gold \
         --harp-consensus-protocol bdr \
         --platform aws --region eu-west-1 --instance-type t3.micro \
         --distribution Debian-minimal
```

You must specify `--architecture BDR-Always-ON`. (In the example
above, it is the only option required to produce a working
configuration.)

You also must specify `--layout layoutname` to set one of the supported BDR
use-case variations. The current options are bronze, silver, gold, and
platinum. The bronze, gold and platinum layouts have a BDR witness node
to ensure odd number of nodes for Raft consensus majority. Witness nodes do
not participate in the data replication.

You must specify `--harp-consensus-protocol protocolname`. The supported
protocols are bdr and etcd; see [`Configuring HARP`](harp.md) for more details.

You may optionally specify `--bdr-database dbname` to set the name of
the database with BDR enabled (default: bdrdb).

You may optionally specify `--enable-camo` to set the pair of BDR
primary instances in each region to be each other's CAMO partners.

Please note we enable HARP2 by default in BDR-Always-ON architecture.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
