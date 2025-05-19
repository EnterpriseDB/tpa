---
description: Configuring a PGD-S cluster with TPA.
---

# PGD-S

!!! Note
    This architecture is for Postgres Distributed 6 only.
    If you require PGD 5 please use [PGD-Always-ON](architecture-PGD-Always-ON.md)
    or [Lightweight](architecture-PGD-Lightweight.md).

    EDB Postgres Distributed 6 in a PGD Essential configuration,
    suitable for use in test and production.

    This architecture requires an EDB subscription.
    All software will be sourced from [EDB Repos 2.0](edb_repositories.md).

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

<br/><br/>

### More detail about PGD-S configuration

A PGD-S cluster comprises a single location with three data nodes.

You may optionally specify `--bdr-database dbname` to set the name of
the database with BDR enabled (default: bdrdb).

You may optionally specify `--enable-pgd-probes [{http, https}]` to
enable http(s) api endpoints that will allow to easily probe proxy's health.

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
