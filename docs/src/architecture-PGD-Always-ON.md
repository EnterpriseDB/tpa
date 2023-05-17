# PGD-Always-ON

EDB Postgres Distributed 5 in an Always-ON configuration,
suitable for use in test and production.

This architecture is valid for use with EDB Postgres Distributed 5 only
and requires a subscription to [EDB Repos 2.0](2q_and_edb_repositories.md).

## Cluster configuration

### Overview of configuration options

An example invocation of `tpaexec configure` for this architecture
is shown below.

```shell
tpaexec configure ~/clusters/pgd-ao \
         --architecture PGD-Always-ON \
         --edb-postgres-extended 15 \
         --platform aws --instance-type t3.micro \
         --distribution Debian \
         --pgd-proxy-routing global \
         --location-names dc1 dc2 dc3 \
         --witness-only-location dc3 \
         --data-nodes-per-location 2
```

You can list all available options using the help command.

```shell
tpaexec configure --architecture PGD-Always-ON --help
```

The table below describes the mandatory options for PGD-Always-ON
and additional important options.
More detail on the options is provided in the following section.

#### Mandatory Options

| Options                                               | Description                                                                                 |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `--architecture` (`-a`)                               | Must be set to `PGD-Always-ON`                                                              |
| Postgres flavour and version (e.g. `--postgresql 15`) | A valid [flavour and version specifier](tpaexec-configure.md#postgres-flavour-and-version). |
| `--pgd-proxy-routing`                                 | Must be either `global` or `local`.                                                         |

<br/><br/>


#### Additional Options

| Options                          | Description                                                                                                 | Behaviour if omitted                                        |
|----------------------------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| `--platform`                     | One of `aws`, `docker`, `bare`.                                                                             | Defaults to `aws`.                                          |
| `--location-names`               | A space-separated list of location names. The number of locations is equal to the number of names supplied. | TPA will configure a single location with three data nodes. |
| `--witness-only-location`        | A location name, must be a member of `location-names`.                                                      | No witness-only location is added.                          |
| `--data-nodes-per-location`      | The number of data nodes in each location, must be at least 2.                                              | Defaults to 3.                                              |
| `--add-proxy-nodes-per-location` | The number of proxy nodes in each location.                                                                 | PGD-proxy will be installed on each data node.              |
| `--enable-camo`                  | Sets two data nodes in each location as CAMO partners.                                                      | CAMO will not be enabled.                                   |
| `--bdr-database`                 | The name of the database to be used for replication.                                                        | Defaults to `bdrdb`.                                        |

<br/><br/>

### More detail about PGD-Always-ON configuration

A PGD-Always-ON cluster comprises a number of locations, preferably odd,
each with the same number of data nodes, again preferably odd. If you do
not specify any `--location-names`, the default is to use a single
location with three data nodes.

Location names for the cluster are specified as
`--location-names dc1 dc2 …`. A location represents an independent
data centre that provides a level of redundancy, in whatever way
this definition makes sense to your use case. For example, AWS
regions, your own data centres, or any other designation to identify
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

You may optionally specify `--bdr-database dbname` to set the name of
the database with BDR enabled (default: bdrdb).

You may optionally specify `--enable-camo` to set two data nodes in
each region as CAMO partners.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
