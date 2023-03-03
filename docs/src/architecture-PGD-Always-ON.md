# PGD-Always-ON

EDB Postgres Distributed 5 in an Always-ON configuration,
suitable for use in test and production.

This architecture is valid for use with PGD version 5 only and requires
a subscription to [EDB Repos 2.0](2q_and_edb_repositories.md).

## Cluster configuration

```
[tpa]$ tpaexec configure ~/clusters/pgd-ao \
         --architecture PGD-Always-ON \
         --location-names eu-west-1 eu-north-1 eu-central-1 \
         --data-nodes-per-location 2 \
         --active-locations eu-west-1 eu-central-1 \
         --witness-only-location eu-north-1 \
         --platform aws --instance-type t3.micro \
         --distribution Debian-minimal \
         --edbpge 15
```

You must specify `--architecture PGD-Always-ON`.

You must specify a list of location names for the cluster with
`--location-names dc1 dc2 dc3`.

A location represents an independent data centre that provides a level
of redundancy, in whatever way this definition makes sense to your use
case. For example, AWS regions, your own data centres, or any other
designation to identify where your servers are hosted.

(If you are using TPA to provision an AWS cluster, the locations will be
mapped to separate availability zones within the `--region` you specify.
You may specify multiple `--regions`, but TPA does not currently set up
VPC peering to allow instances in different regions to communicate with
each other. For a multi-region cluster, you will need to set up VPC
peering yourself.)

A PGD-Always-ON cluster comprises a number of locations, preferably odd,
each with the same number of data nodes, again preferably odd. If you do
not specify any --location-names, the default is to use a single
location with three data nodes.

Use `--data-nodes-per-location N` to specify a different number of data
nodes. The minimum number is 2.

If you specify an even number of data nodes per location, TPA will add
an extra witness node to each location automatically. This retains the
ability to establish reliable consensus while allowing cost savings (a
witness has minimal hardware requirements compared to the data nodes).

A cluster with only two locations would entirely lose the ability to
establish global consensus if one of the locations were to fail. We
recommend adding a third witness-only location (which contains no data
nodes, only a witness node, again used to reliably establish consensus).
Use `--witness-only-location loc` to designate one of your locations as
a witness. (This location must not be among the `--active-locations`.)

By default, each location will also have separate PGD-Proxy instances.
You may specify `--cohost-proxies` to run PGD-Proxy on the data nodes.

By default, TPA will configure PGD-Proxy to use global connection
routing, i.e., to elect a write lead from all available data nodes
across all locations. You may specify `--active-locations l2 l3` to
limit connection routing to nodes in the specified locations. This will
enable subgroup RAFT and proxy routing for those locations only.

You may optionally specify `--database-name dbname` to set the name of
the database with BDR enabled (default: bdrdb).

You may optionally specify `--enable-camo` to set the pair of BDR
primary instances in each region to be each other's CAMO partners.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
