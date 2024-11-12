---
description: Configuring a PGD Lightweight cluster with TPA.
---

# PGD Lightweight

!!! Note
    This architecture is for Postgres Distributed 5 only.
    If you require PGD 4 or 3.7 please use [BDR-Always-ON](BDR-Always-ON.md).

    EDB Postgres Distributed 5 in a Lightweight configuration,
    suitable for use in test and production.

    This architecture requires an EDB subscription.
    All software will be sourced from [EDB Repos 2.0](edb_repositories.md).

## Cluster configuration

### Overview of configuration options

An example invocation of `tpaexec configure` for this architecture
is shown below.

```bash
    tpaexec configure ~/clusters/pgd-lw \
        --architecture Lightweight \
        --edb-postgres-extended 15 \
        --platform aws --instance-type t3.micro \
        --distribution Debian \
        --location-names main dr \
```

You can list all available options using the help command.

```bash
tpaexec configure --architecture Lightweight --help
```

The table below describes the mandatory options for PGD-Always-ON
and additional important options.
More detail on the options is provided in the following section.

#### Mandatory Options

| Options                                               | Description                                                                                 |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `--architecture` (`-a`)                               | Must be set to `Lightweight`                                                              |
| Postgres flavour and version (e.g. `--postgresql 15`) | A valid [flavour and version specifier](tpaexec-configure.md#postgres-flavour-and-version). |

<br/><br/>

#### Additional Options

| Options                          | Description                                                                                                 | Behaviour if omitted                                        |
|----------------------------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| `--platform`                     | One of `aws`, `docker`, `bare`.                                                                             | Defaults to `aws`.                                          |
| `--location-names`               | A space-separated list of location names. The number of locations is equal to the number of names supplied. | TPA will configure a single location with three data nodes. |
| `--add-proxy-nodes-per-location` | The number of proxy nodes in each location.                                                                 | PGD-proxy will be installed on each data node.              |
| `--bdr-database`                 | The name of the database to be used for replication.                                                        | Defaults to `bdrdb`.                                        |
| `--enable-pgd-probes`            | Enable http(s) api endpoints for pgd-proxy such as `health/is-ready` to allow probing proxy's health.       | Disabled by default.                                        |
| `--proxy-listen-port`            | The port on which proxy nodes will route traffic to the write leader.                                       | Defaults to 6432                                            |
| `--proxy-read-only-port`         | The port on which proxy nodes will route read-only traffic to shadow nodes.                                 | Defaults to 6433|

<br/><br/>

### More detail about Lightweight configuration

A PGD Lightweight cluster comprises 2 locations, with a primary active location containing 2 nodes and a disaster recovery (dr) location with a single node.

Location names for the cluster are specified as
`--location-names primary dr`. A location represents an independent
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

By default, every data node (in every location) will also run PGD-Proxy
for connection routing. To create separate PGD-Proxy instances instead,
use `--add-proxy-nodes-per-location 3` (or however many proxies you want
to add).

Global routing will make every proxy route to a single write leader, elected amongst all available data nodes across all locations.

You may optionally specify `--bdr-database dbname` to set the name of
the database with BDR enabled (default: bdrdb).

You may optionally specify `--enable-pgd-probes [{http, https}]` to
enable http(s) api endpoints that will allow to easily probe proxy's health.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
