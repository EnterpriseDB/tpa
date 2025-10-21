---
description: Configuring a PGD-S cluster with TPA.
---

# PGD-S

!!!Note
This architecture is for Postgres Distributed 6 only.
If you require PGD 5 please use [PGD-Always-ON](architecture-PGD-Always-ON/).
!!!

EDB Postgres Distributed 6 in a PGD Essential (PGD-S) configuration
suitable for use in test and production.

This architecture requires an EDB subscription.
All software is sourced from [EDB Repos 2.0](reference/edb_repositories/).


## Cluster configuration

### Overview of configuration options

An example invocation of `tpaexec configure` for this architecture
is shown below.

```bash
tpaexec configure ~/clusters/pgd-s \
    --architecture PGD-S
    --edb-postgres-extended 15 \
    --platform aws --instance-type t3.micro \
    --distribution Debian \
```

You can list all available options using the help command.

```bash
tpaexec configure --architecture PGD-S --help
```

The table below describes the mandatory options for PGD-S
and additional important options.
More detail on the options is provided in the following section.

#### Mandatory Options

| Options                                               | Description                                                                                 |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `--architecture` (`-a`)                               | Must be set to `PGD-S`                                                              |
| Postgres flavour and version (e.g. `--postgresql 15`) | A valid [flavour and version specifier](tpaexec-configure.md#postgres-flavour-and-version). |

<br/><br/>

#### Additional Options

| Options                          | Description                                                                                                 | Behaviour if omitted                                        |
|----------------------------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| `--platform`                     | One of `aws`, `docker`, `bare`.                                                                             | Defaults to `aws`.                                          |
| `--bdr-database`                 | The name of the database to be used for replication.                                                        | Defaults to `bdrdb`.                                        |
| `--layout`                       | `standard` or `near-far`                                                                                    | Defaults to `standard`                                      |
| `--add-subscriber-only-nodes`    | The number of subscriber-only nodes to add, up to 10.                                                       | Defaults to 0                                               |
| `--read-write-port`              | The port for Connection Manager to listen on for read-write connections.                                    | Left empty in config.yml, allowing default of the postgres port + 1000 |
| `--read-only-port`               | The port for Connection Manager to listen on for read-only connections.                                     | Left empty in config.yml, allowing default of the read-write port + 1  |
| `--http-port`                    | The port for Connection Manager to listen on for http api connections.                                      | Left empty in config.yml, allowing default of the read-write port + 2    |
| `--use https`                    | Enable https for Connection Manager's http api                                                              | https is not enabled                                        |

<br/><br/>

### More detail about PGD-S configuration

A PGD-S cluster has three data nodes. In the `standard` layout the nodes
are all in the same location; in the `near-far` layout two nodes are in
the primary location and the other is in a secondary location. See
the [PGD
documentation](https://www.enterprisedb.com/docs/pgd/latest/essential-how-to/)
for more information about the two layouts.

The cluster also contains one barman node and up to 10 subscriber-only
nodes, controlled by the `--add-subscriber-only-nodes` parameter. These
are always in the primary location.

You may optionally specify `--bdr-database dbname` to set the name of
the database with BDR enabled (default: bdrdb).


You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
