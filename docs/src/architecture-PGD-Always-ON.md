# PGD-Always-ON

EDB Postgres Distributed 5 in an Always-ON configuration,
suitable for use in test and production.

This architecture is valid for use with PGD version 5 only and requires
a subscription to [EDB Repos 2.0](2q_and_edb_repositories.md).

## Cluster configuration

```
# Example invocation
[tpa]$ tpaexec configure ~/clusters/pgd-ao \
         --architecture PGD-Always-ON \
         --location-names dc1 dc2 dc3 \
         --pgd-proxy-routing local \
         --witness-only-location dc3 \
         --data-nodes-per-location 2 \
         --platform aws --instance-type t3.micro \
         --distribution Debian \
         --edbpge 15

# Show all available options
[tpa]$ tpaexec configure --architecture PGD-Always-ON --help
```

You must specify `--architecture PGD-Always-ON`.

You must specify a list of location names for the cluster with
`--location-names dc1 dc2 …`.

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
not specify any `--location-names`, the default is to use a single
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
a witness.

By default, every data node (in every location) will also run PGD-Proxy
for connection routing. To create separate PGD-Proxy instances instead,
use `--add-proxy-nodes-per-location 3` (or however many proxies you want
to add).

Depending on your use-case, you must specify `--pgd-proxy-routing local`
or `global` to configure how PGD-Proxy will route connections to a write
leader. Local routing will make every PGD-Proxy route to a write leader
within its own location (suitable for geo-sharding applications). Global
routing will make every proxy route to a single write leader, elected
amongst all available data nodes across all locations.

You may optionally specify `--database-name dbname` to set the name of
the database with BDR enabled (default: bdrdb).

You may optionally specify `--enable-camo` to set the pair of BDR
primary instances in each region to be each other's CAMO partners.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
