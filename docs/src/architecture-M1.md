# M1

A Postgres cluster with a primary and a streaming replica, one Barman
server, and any number of additional replicas cascaded from the first
one. This architecture is suitable for testing, demonstrating and
learning. We plan to release a production primary/standby architecture
for TPA in the near future.

In default configuration this architecture uses open source software
only. To use subscription-only EDB software with this architecture
requires credentials for EDB Repos 1.0. If you choose EDB Advanced
Server (EPAS) you will also require credentials for the legacy
2ndQuadrant repos.
See [How TPA uses 2ndQuadrant and EDB repositories](2q_and_edb_repositories.md)
for more detail on this topic.

## Default layout

By default, the primary has one read-only replica attached in the same
location; the replica, in turn, has one cascaded replica attached in a
different location, where the Barman server is also configured to take
backups from the primary.

![Cluster with cascading replication](images/m1.png)

If there is an even number of Postgres nodes, the Barman node is
additionally configured as a witness. This ensures that the
number of nodes is always odd, which is convenient when
enabling automatic failover.

## Cluster configuration

### Overview of configuration options

An example invocation of `tpaexec configure` for this architecture
is shown below.

```shell
tpaexec configure ~/clusters/m1 \
         --architecture M1 \
         --platform aws --region eu-west-1 --instance-type t3.micro \
         --distribution Debian \
         --postgresql 14
```

You can list all available options using the help command.

```shell
tpaexec configure --architecture M1 --help
```

The tables below describe the mandatory options for M1
and additional important options.
More detail on the options is provided in the following section.

#### Mandatory Options

| Parameter                                             | Description                                                                                 |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `--architecture` (`-a`)                               | Must be set to `M1`.                                                                        |
| Postgres flavour and version (e.g. `--postgresql 15`) | A valid [flavour and version specifier](tpaexec-configure.md#postgres-flavour-and-version). |

<br/><br/>

#### Additional Options

| Parameter                 | Description                                              | Behaviour if omitted |
|---------------------------|----------------------------------------------------------|----------------------|
| `--platform`              | One of `aws`, `docker`, `bare`.                          | Defaults to `aws`.   |
| `--num-cascaded-replicas` | The number of cascaded replicas from the first replica.  | Defaults to 1.       |
| `--enable-efm`            | Configure Failover Manager as the cluster failover manager. | TPA will select EFM<br/>as the failover manager<br/>for EPAS, and repmgr<br/>for all other flavours.  |


<br/><br/>

### More detail about M1 configuration

You may optionally specify `--num-cascaded-replicas N` to request N
cascaded replicas (including 0 for none; default: 1).

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
