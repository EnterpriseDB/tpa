# PGD-Always-ON

EDB Postgres Distributed 5 in an Always-ON configuration,
suitable for use in test and production.

This architecture is valid for use with EDB Postgres Distributed version 5 only
and requires a subscription to [EDB Repos 2.0](2q_and_edb_repositories.md).

## Cluster configuration

### Overview of configuration options

This example shows an invocation of `tpaexec configure` for this architecture:

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

You can list all available options using the `help` option.

```shell
tpaexec configure --architecture PGD-Always-ON --help
```

#### Mandatory options

| Options                                               | Description                                                                                 |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `--architecture` (`-a`)                               | Must be set to `PGD-Always-ON`                                                              |
| Postgres flavour and version (e.g. `--postgresql 15`) | A valid [flavour and version specifier](tpaexec-configure.md#postgres-flavour-and-version). |
| `--pgd-proxy-routing`                                 | Must be either `global` or `local`.                                                         |

<br/><br/>


#### Additional options

| Options                          | Description                                                                                                 | Behavior if omitted                                        |
|----------------------------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| `--platform`                     | One of `aws`, `docker`, `bare`.                                                                             | Defaults to `aws`.                                          |
| `--location-names`               | A space-separated list of location names. The number of locations is equal to the number of names supplied. | TPA will configure a single location with three data nodes. |
| `--witness-only-location`        | A location name, must be a member of `location-names`.                                                      | No witness-only location is added.                          |
| `--data-nodes-per-location`      | The number of data nodes in each location, must be at least 2.                                              | Defaults to 3.                                              |
| `--add-proxy-nodes-per-location` | The number of proxy nodes in each location.                                                                 | PGD-proxy will be installed on each data node.              |
| `--enable-camo`                  | Sets two data nodes in each location as CAMO partners.                                                      | CAMO will not be enabled.                                   |
| `--bdr-database`                 | The name of the database to be used for replication.                                                        | Defaults to `bdrdb`.                                        |
| `--enable-pgd-probes`            | Enable http(s) API endpoints like `health/is-ready` to probe pgd-proxy's health.       | Disabled by default.                                        |

<br/><br/>

### More detail about PGD-Always-ON configuration

A PGD-Always-ON cluster comprises a number of locations, preferably odd.
Each location has the same number of data nodes, also preferably odd. If you don't
specify any `--location-names`, the default is to use a single
location with three data nodes.

You can specify location names for the cluster with
`--location-names dc1 dc2 …`. A location represents an independent
data center that provides a level of redundancy, in whatever way
this definition makes sense to your use case. Examples include AWS
regions, your own data centers, or any other designation to identify
where your servers are hosted.

!!! Note for AWS users
    If you're using TPA to provision an AWS cluster, the locations will
    be mapped to separate availability zones in the `--region` you
    specify.
    You can specify multiple `--regions`, but TPA doesn't currently set
    up VPC peering to allow instances in different regions to
    communicate with each other. For a multi-region cluster, you must
    set up VPC peering yourself.

Use `--data-nodes-per-location N` to specify the number of data
nodes in each location. The minimum number is 2. The default is 3.

If you specify an even number of data nodes per location, TPA 
adds an extra witness node to each location. The witness 
preserves the ability to reliably establish consensus without 
the hardware requirements and extra cost of another data node.

A cluster with only two locations would entirely lose the ability to
establish global consensus if one of the locations were to fail. 
You can retain the ability to establish consensus despite a single-location failure.
To do so, we recommend adding a third witness-only location that contains only 
a witness node. Use `--witness-only-location loc` to designate one of 
your locations as a witness.

By default, every data node in every location also runs PGD Proxy
for connection routing. To create separate PGD Proxy instances instead,
use `--add-proxy-nodes-per-location 3` (or however many proxies you want
to add).

Depending on your use case, you must specify `--pgd-proxy-routing local`
or `global` to configure how PGD Proxy routes connections to a write
leader. Local routing makes every PGD Proxy route to a write leader
within its own location (suitable for geosharding applications). Global
routing makes every proxy route to a single write leader, elected
among all available data nodes across all locations.

You can optionally specify:

- `--bdr-database dbname` to set the name of the database with BDR enabled (default: bdrdb)

- `--enable-camo` to set two data nodes in each region as CAMO partners

- `--enable-pgd-probes [{http, https}]` to enable http(s) api endpoints that allow you to easily probe proxy's health

You can also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
