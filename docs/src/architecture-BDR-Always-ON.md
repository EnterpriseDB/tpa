# BDR-Always-ON

EDB Postgres Distributed 3.7 or 4 in an Always-ON
configuration is suitable for use in test and production.

This architecture requires a subscription to the legacy 2ndQuadrant
repositories, and some options require a subscription to EDB Repos 1.0.
See [How TPA uses 2ndQuadrant and EDB repositories](2q_and_edb_repositories.md)
for more detail.

The BDR-Always-ON architecture has four variants, which can be
selected with the `--layout` configure option:

- `bronze`: 2×bdr+primary, bdr+witness, barman, 2×harp-proxy

- `silver`: bronze, with bdr+witness promoted to bdr+primary, and barman
moved to separate location

- `gold`: two symmetric locations with 2×bdr+primary, 2×harp-proxy,
and barman each; plus a bdr+witness in a third location

- `platinum`: gold, but with one bdr+readonly (logical standby) added to
each of the main locations

See EDB's Postgres Distributed Always On Architectures
[whitepaper](https://www.enterprisedb.com/promote/bdr-always-on-architectures)
for the detailed layout diagrams.

This architecture is meant for use with PGD versions 3.7 and 4.

## Cluster configuration

### Overview of configuration options

This example shows an invocation of `tpaexec configure` for this architecture:

```shell
tpaexec configure ~/clusters/bdr \
         --architecture BDR-Always-ON \
         --platform aws --region eu-west-1 --instance-type t3.micro \
         --distribution Debian \
         --edb-postgres-advanced 14 --redwood
         --layout gold \
         --harp-consensus-protocol bdr
```

You can list all available options using the `help` command.

```shell
tpaexec configure --architecture BDR-Always-ON --help
```

#### Mandatory options

| Option                                                | Description                                                                                 |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `--architecture` (`-a`)                               | Must be set to `BDR-Always-ON`.                                                             |
| Postgres flavour and version (e.g., `--postgresql 14`) | A valid [flavour and version specifier](tpaexec-configure.md#postgres-flavour-and-version). |
| `--layout`                                            | One of `bronze`, `silver`, `gold`, `platinum`.                                              |
| `--harp-consensus-protocol`                           | One of `bdr`, `etcd`.                                                                       |

<br/><br/>

#### Additional options

| Option                       | Description                                                                                           | Behavior if omitted      |
|------------------------------|-------------------------------------------------------------------------------------------------------|---------------------------|
| `--platform`                 | One of `aws`, `docker`, `bare`.                                                                       | Defaults to `aws`.        |
| `--enable-camo`              | Sets two data nodes in each location as CAMO partners.                                                | CAMO isn't enabled. |
| `--bdr-database`             | The name of the database to be used for replication.                                                  | Defaults to `bdrdb`.      |
| `--enable-harp-probes`       | Enable http(s) api endpoints for harp such as `health/is-ready` to allow probing harp's health.      | Disabled by default.      |
<br/><br/>

### More detail about BDR-Always-ON configuration

You must specify `--layout layoutname` to set one of the supported BDR
use-case variations. The permitted arguments are `bronze`, `silver`, `gold`, and
`platinum`. The bronze, gold, and platinum layouts have a PGD witness node
to ensure an odd number of nodes for Raft consensus majority. Witness nodes don't
participate in the data replication.

You must specify `--harp-consensus-protocol protocolname`. The supported
protocols are bdr and etcd. See [`Configuring HARP`](harp.md) for more details.

You can optionally specify `--bdr-database dbname` to set the name of
the database with PGD enabled (default: `bdrdb`).

You can optionally specify `--enable-camo` to set the pair of PGD
primary instances in each region to be each other's CAMO partners.

You can optionally specify `--enable-harp-probes [{http, https}]` to
enable http(s) api endpoints that allow you to easily probe harp's health.

!!! Note
    We enable HARP2 by default in BDR-Always-ON architecture.

You can also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
