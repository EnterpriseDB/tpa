# PGD-Always-ON

EDB Postgres Distributed in an Always-ON configuration, intended for use in production.

## Cluster configuration

```
[tpa]$ tpaexec configure ~/clusters/pgd-ao \
         --architecture PGD-Always-ON \
         --location-names eu-west-1 eu-north-1 eu-central-1 \
         --data-nodes-per-location 2 \
         --witness-node-per-location \
         --active-locations eu-west-1 eu-central-1 \
         --witness-only-location eu-north-1 \
         --platform aws --instance-type t3.micro \
         --distribution Debian-minimal
```

You must specify `--architecture PGD-Always-ON`.

You must also specify list of locations that can be mapped to cloud provider
regions, or availability zones or your vm locations, or any other physical
location description you use.

You may optionally specify how many data nodes there should be per location
using `--data-nodes-per-location`. Minimum number of data nodes is 2, if not
specified, this defaults to 3.

You may optionally specify which locations are active, meaning, accepting writes,
using `--active-locations`. If not specified this defaults to globally handled
write connection routing, which elects write lead from all available nodes
across all locations. Empty list can be specified, this disable the builtin
connection routing management and will not configure any PGD-Proxies.

You may optionally specify whether there should be witness node in every location
using `--witness-node-per-location`. The default behavior depends on value of
`--data-nodes-per-location`, with `--data-nodes-per-location` set to 2, this
will default to true, otherwise it's false by default.

You may also specify a special location that does not contain any data nodes
but only has single witness node used for improved availability of consensus
using `–-witness-only-location` parameter. This location cannot be among the
active locations list.

You may optionally specify `--cohost-proxies` to configure PGD-Proxy instances
to run on the same hosts as data nodes.

You may optionally specify `--node-group-name groupname` to set the
name of the cluster-level BDR node group (default: bdrgroup). This will
be also used as prefix for per-location data groups.

You may optionally specify `--database-name dbname` to set the name of
the database with BDR enabled (default: bdrdb).

You may optionally specify `--enable-camo` to set the pair of BDR
primary instances in each region to be each other's CAMO partners.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
