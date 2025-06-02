---
description: Configuring a PGD-X cluster with TPA.
---

# PGD-X

!!! Note
This architecture is for Postgres Distributed 6 only.
If you require PGD 5 please use [PGD-Always-ON](architecture-PGD-Always-ON.md).
!!!

EDB Postgres Distributed 6 in an Expanded configuration
suitable for use in test and production.

This architecture requires an EDB subscription.
All software will be sourced from [EDB Repos 2.0](edb_repositories.md).

## Cluster configuration

### Overview of configuration options

An example invocation of `tpaexec configure` for this architecture
is shown below.

```shell
tpaexec configure ~/clusters/pgd-x \
         --architecture PGD-X \
         --edb-postgres-extended 15 \
         --platform aws --instance-type t3.micro \
         --distribution Debian \
         --pgd-routing global \
         --location-names dc1 dc2 dc3 \
         --witness-only-location dc3 \
         --data-nodes-per-location 2
```

You can list all available options using the help command.

```shell
tpaexec configure --architecture PGD-X --help
```

The table below describes the mandatory options for PGD-X
and additional important options.
More detail on the options is provided in the following section.

#### Mandatory Options

| Options                                               | Description                                                                                 |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `--architecture` (`-a`)                               | Must be set to `PGD-X`                                                              |
| Postgres flavour and version (e.g. `--postgresql 15`) | A valid [flavour and version specifier](tpaexec-configure.md#postgres-flavour-and-version). |
| `--pgd-routing`                                 | Must be either `global` or `local`.                                                         |

<br/><br/>


#### Additional Options

| Options                          | Description                                                                                                 | Behaviour if omitted                                        |
|----------------------------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| `--platform`                     | One of `aws`, `docker`, `bare`.                                                                             | Defaults to `aws`.                                          |
| `--location-names`               | A space-separated list of location names. The number of locations is equal to the number of names supplied. | TPA will configure a single location with three data nodes. |
| `--witness-only-location`        | A location name, must be a member of `location-names`.                                                      | No witness-only location is added.                          |
| `--data-nodes-per-location`      | The number of data nodes in each location, must be at least 2.                                              | Defaults to 3.                                              |
| `--enable-camo`                  | Sets two data nodes in each location as CAMO partners.                                                      | CAMO will not be enabled.                                   |
| `--bdr-database`                 | The name of the database to be used for replication.                                                        | Defaults to `bdrdb`.                                        |
| `--enable-pgd-probes`            | Enable http(s) api endpoints for pgd-proxy such as `health/is-ready` to allow probing proxy's health.       | Disabled by default.                                        |
| `--proxy-listen-port`            | The port on which proxy nodes will route traffic to the write leader.                                       | Defaults to 6432                                            |
| `--proxy-read-only-port`         | The port on which proxy nodes will route read-only traffic to shadow nodes.                                 | Defaults to 6433

<br/><br/>

### More detail about PGD-X configuration

A PGD-X cluster comprises a number of locations, preferably odd,
each with the same number of data nodes, again preferably odd. If you do
not specify any `--location-names`, the default is to use a single
location with three data nodes.

Location names for the cluster are specified as
`--location-names dc1 dc2 …`. A location represents an independent
data center that provides a level of redundancy, in whatever way
this definition makes sense to your use case. For example, AWS
regions, your own data centers, or any other designation to identify
where your servers are hosted.

!!! Note for AWS users
    If you are using TPA to provision an AWS cluster, the locations will
    be mapped to separate availability zones within the `--region` you
    specify.
    You may specify multiple `--regions`, but TPA does not currently set
    up VPC peering to allow instances in different regions to
    communicate with each other. For a multi-region cluster, you will
    need to set up VPC peering yourself.

Use `--data-nodes-per-location N` to specify the number of data
nodes in each location. The minimum number is 2, the default is 3.

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

Depending on your use-case, you must specify `--pgd-routing local`
or `global` to configure how Connection Manager will route connections to a write
leader. Local routing will make every Connection Manager route to a write leader
within its own location (suitable for geo-sharding applications). Global
routing will make every Connection Manager route to a single write leader, elected
amongst all available data nodes across all locations.

You may optionally specify `--bdr-database dbname` to set the name of
the database with BDR enabled (default: bdrdb).

You may optionally specify `--enable-camo` to set two data nodes in
each region as CAMO partners.

You may optionally specify `--enable-pgd-probes [{http, https}]` to
enable http(s) api endpoints that will allow to easily probe proxy's health.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
