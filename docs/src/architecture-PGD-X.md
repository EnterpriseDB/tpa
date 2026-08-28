---
description: Configuring a PGD-X cluster with TPA.
---

# PGD-X

!!!Note
This architecture is for Postgres Distributed 6 only.
If you require PGD 5 please use [PGD-Always-ON](architecture-PGD-Always-ON/).
!!!

EDB Postgres Distributed 6 in a PGD Expanded (PGD-X) configuration
suitable for use in test and production.

This architecture requires an EDB subscription.
All software is sourced from [EDB Repos 2.0](reference/edb_repositories/).

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
| Postgres flavour and version (e.g. `--postgresql 15`) | A valid [flavour and version specifier](tpaexec-configure.md#postgres-flavour-and-version). Supports Postgres 14-18. |
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
| `--read-write-port`              | The port for Connection Manager to listen on for read-write connections.                                    | Left empty in config.yml, allowing default of the postgres port + 1000 |
| `--read-only-port`               | The port for Connection Manager to listen on for read-only connections.                                     | Left empty in config.yml, allowing default of the read-write port + 1  |

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

You may optionally change the ports that Connection Manager listens on
for read-write and read-only connections, either with the
`--read-write-port` and `--read-only-port` options to `tpaexec configure`
(see the [Additional Options](#additional-options) table) or by editing
`config.yml` afterwards. The two ports must differ from each other and
from the Postgres port (`postgres_port`) for the cluster.

Connection Manager reads these settings from whichever BDR group has
routing enabled, so you must define them under the `options` for that
group:

- with `--pgd-routing global`, the top-level group;
- with `--pgd-routing local`, each location subgroup.

Ports defined on a group that does not have routing enabled have no
effect.

With global routing, the ports belong to the top-level group:

```yaml
cluster_vars:
  postgres_port: 5432
  bdr_node_groups:
  - name: <cluster-name>
    options:
      read_write_port: 7432
      read_only_port: 7433
      enable_routing: true
  - name: first_subgroup
    parent_group_name: <cluster-name>
    options:
      location: first
      enable_routing: false
```

With local routing, they belong to each location subgroup instead:

```yaml
cluster_vars:
  postgres_port: 5432
  bdr_node_groups:
  - name: <cluster-name>
    options:
      enable_routing: false
  - name: first_subgroup
    parent_group_name: <cluster-name>
    options:
      location: first
      read_write_port: 7432
      read_only_port: 7433
      enable_routing: true
```

!!! Note
    With `--pgd-routing local`, `tpaexec configure` writes
    `--read-write-port` and `--read-only-port` to the top-level group. You
    must move them to the location subgroups, as shown above, for them to
    take effect.

If you do not set these options at all, Connection Manager listens on
`postgres_port` + 1000 for read-write connections and `postgres_port` +
1001 for read-only connections.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
