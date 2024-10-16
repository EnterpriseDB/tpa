---
description: Configuring the M1 architecture with TPA.
---

# M1

A Postgres cluster with a single primary node and physical replication
to a number of standby nodes including backup and failover management.

This architecture is suitable for production and is also suited to
testing, demonstrating and learning due to its simplicity and ability to
be configured with no proprietary components.

If you select subscription-only EDB software with this architecture
it will be sourced from EDB Repos 2.0 and you will need to 
[provide a token](edb_repositories.md).

## Failover management

The M1 architecture always includes a failover manager. Supported
options are repmgr, EDB Failover Manager (EFM) and Patroni. In all
cases, the failover manager will be configured by default to ensure that
a replica will be promoted to take the place of the primary should the
primary become unavailable. 

### Application failover

The M1 architecture does not generally provide an automatic facility to
reroute application traffic to the primary. There are several ways you
can add this capability to your cluster.

In TPA:

* If you choose repmgr as the failover manager and enable PgBouncer, you
  can include the `repmgr_redirect_pgbouncer: true` hash under
  `cluster_vars` in `config.yml`. This causes repmgr to automatically
  reconfigure PgBouncer to route traffic to the new primary on failover.
  
* If you choose EFM as the failover manager, you can use the
  `efm_conf_settings` hash under `cluster_vars` in `config.yml` to
  [configure EFM to use a virtual IP address
  (VIP)](/efm/latest/04_configuring_efm/05_using_vip_addresses/). This
  is an additional IP address which will always route to the primary
  node.

!!! Note
We plan to make the option to automatically redirect pgBouncer to the
primary available for all failover managers in a future release of TPA.
!!!

Outside of TPA:

* Place an appropriate proxy or load balancer between the cluster and
  you application and configure your selected failover manager to update
  the it with the route to the new primary on failover.

* Handle failover at the application itself, for example buy using
  multi-hosting connection strings.

### Backup failover

Barman backup nodes will not be automatically adjusted to
target the new primary in the event of failover, instead it will remain
connected to the original primary. 

!! This stuff is wrong I think and needs update!!
If you are performing a manual
failover and wish to connect the backup to the new primary, you may
simply re-run `tpaexec deploy`. If you wish to automatically change the
backup source, you should implement this using your selected failover
manager as noted above.

## Cluster configuration

### Overview of configuration options

An example invocation of `tpaexec configure` for this architecture
is shown below.

```shell
tpaexec configure ~/clusters/m1 \
         --architecture M1 \
         --platform aws --region eu-west-1 --instance-type t3.micro \
         --distribution Debian \
         --postgresql 14 \
         --failover-manager repmgr \
         --data-nodes-per-location 3
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
| One of: <br> - `--failover-manager {efm, repmgr, patroni}`<br>- `--enable-efm`<br> - `--enable-repmgr`<br>- `--enable-patroni`  | Select the failover manager from [`efm`](efm.md), [`repmgr`](repmgr.md) and [`patroni`](patroni.md).                                                  |

<br/><br/>

#### Additional Options

| Parameter                 | Description                                                                                                       | Behaviour if omitted                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| `--platform`              | One of `aws`, `docker`, `bare`.                                                                                   | Defaults to `aws`.                                                                                   |
| `--location-names` | A space-separated list of location names. The number of active locations is equal to the number of names supplied, minus one for each of the witness-only location and the single-node location if they are requested. | A single location called "main" is used. |
| `--primary-location` | The location where the primary server will be. Must be a member of `location-names`. | The first listed location is used. |
| `--data-nodes-per-location` | A number from 1 upwards. In each location, one node will be configured to stream directly from the cluster's primary node, and the other nodes, if present, will stream from that one. | Defaults to 2.
| `--witness-only-location` | A location name, must be a member of `location-names`. | No witness-only location is added. |
| `--single-node-location` | A location name, must be a member of `location-names`. | No single-node location is added. |
| `--enable-haproxy`        | 2 additional nodes will be added as a load balancer layer.<br/>Only supported with Patroni as the failover manager. | HAproxy nodes will not be added to the cluster.                                                      |
| `--enable-pgbouncer`        | PgBouncer will be configured in the Postgres nodes to pool connections for the primary. | PgBouncer will not be configured in the cluster.                                                      |
| `--patroni-dcs`           | Select the Distributed Configuration Store backend for patroni.<br/>Only option is `etcd` at this time. <br/>Only supported with Patroni as the failover manager. | Defaults to `etcd`. |
| `--efm-bind-by-hostname` | Enable efm to use hostnames instead of IP addresses to configure the cluster `bind.address`. | Defaults to use IP addresses |

<br/><br/>

### More detail about M1 configuration

You may also specify any of the options described by
[`tpaexec help configure-options`](tpaexec-configure.md).
