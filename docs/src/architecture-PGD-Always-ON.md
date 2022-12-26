# PGD-Always-ON

EDB Postgres Distributed in an Always-ON configuration, intended for use in production.

This architecture is meant for use with PGD (BDR) version 5 only.

## Cluster configuration

```
[tpa]$ tpaexec configure ~/clusters/pgd-ao \
         --architecture PGD-Always-ON \
         --location-names eu-west-1 eu-north-1 eu-central-1 \
         --data-nodes-per-location 2 \
         --add-witness-node-per-location \
         --active-locations eu-west-1 eu-central-1 \
         --add-witness-only-location eu-north-1 \
         --platform aws --instance-type t3.micro \
         --distribution Debian-minimal
```

You must specify `--architecture PGD-Always-ON`.

You must specify a list of location names for the cluster with
`--location-names dc1 dc2 dc3`.

A location represents an independent data centre that provides a level
of redundancy, in whatever way this definition makes sense to your use
case. For example, AWS regions, or availability zones within a region,
or any other designation to identify where your servers are hosted.

A PGD-Always-ON cluster comprises one or more locations with the same
number of data nodes (if required to establish consensus, there may be
an additional witness node in each location, as well as a single extra
witness-only location). These locations, as many as required, must be
named in the `--location-names` list.

(If you are using TPA to provision an AWS cluster, the locations will be
mapped to separate availability zones within the `--region` you specify.
You may specify multiple `--regions`, but TPA does not currently set up
VPC peering to allow instances in different regions to communicate with
each other. For a multi-region cluster, you will need to set up VPC
peering yourself.)

By default, each location will have three data nodes. You may specify
a different number with `--data-nodes-per-location N`. The minimum
number is 2.

If you have two data nodes per location, each location must also have an
extra witness node, and TPA will add one by default. For any even number
of data nodes >2, you may specify `--add-witness-node-per-location` to
add the extra witness node.

By default, each location will also have separate PGD-Proxy instances.
You may specify `--cohost-proxies` to run PGD-Proxy on the data nodes.

By default, TPA will configure PGD-Proxy to use global connection
routing, i.e., to elect a write lead from all available data nodes
across all locations. You may specify `--active-locations l2 l3` to
limit connection routing to nodes in the specified locations. This will
enable subgroup RAFT and proxy routing for those locations only.

You may optionally specify `--add-witness-only-location loc` to
designate one of the cluster's locations as a special witness-only
location that contains no data nodes and only a single witness node,
used to improve the availability of consensus. This location cannot be
among the active locations list.

You may optionally specify `--database-name dbname` to set the name of
the database with BDR enabled (default: bdrdb).

You may optionally specify `--enable-camo` to set the pair of BDR
primary instances in each region to be each other's CAMO partners.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
