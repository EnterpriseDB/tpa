---
description: Known issues in TPA and their workarounds.
---

# Known issues

This page lists known issues affecting the current version of TPA.
Where one is known, a workaround for each issue is provided.

## The Barman user cannot connect to the database after running `deploy` (TPA-1218)

### Details
If you use TPA 23.35 or later to deploy to a PGD/BDR cluster created
with an earlier version of TPA, the `barman` user's superuser permissions will be
revoked. Consequently, any attempts by this user to connect to the `postgres` database will fail. This will cause the Barman
`check` command to report a failure. 

### Workaround
Use a post-deploy hook to grant superuser to `barman`.

## EFM clusters with more than one location are missing inter-location HBA rules (TPA-1247)

### Details
If you deploy an EFM cluster with more than one location, then perform
the `efm cluster-status` command on one node, you will observe that
`FATAL: password authentication failed for user "efm"` is displayed in
the **Promote Status** section for all nodes not in the same location as
the node on which the command was performed.

This occurs because TPA fails to add the necessary HBA rules for the EFM
user to connect from nodes in one location to nodes in another location.

### Workaround
Use the `postgres_hba_settings` cluster variable to specify one HBA rule
for each node such that the `efm` user and `replication` user can connect from any node to any
other node. For example:

```yaml
postgres_hba_settings:
  - hostssl all efm 192.168.57.12/32 md5
  - hostssl all efm 192.168.57.13/32 md5
  - hostssl all efm 192.168.58.11/32 md5
  - hostssl all efm 192.168.58.12/32 md5
  - hostssl all efm 192.168.58.13/32 md5

  - hostssl replication replication 192.168.57.12/32 md5
  - hostssl replication replication 192.168.57.13/32 md5
  - hostssl replication replication 192.168.58.11/32 md5
  - hostssl replication replication 192.168.58.12/32 md5
  - hostssl replication replication 192.168.58.13/32 md5
```

## Deploy fails on Debian-like instances when a non-current `pem_server_package_version` is specified (TPA-1178)

### Details
TPA installs the PEM server by installing the `edb-pem` metapackage.
On Debian-like systems, using a version specifier with
this package can cause the package manager to attempt an unresolvable
combination of installs resulting in the error:
`Some packages could not be installed. This may mean that you have, requested an impossible situation...`

### Workaround
Consider using the latest version of PEM. If however, you need a
specific version, you can specify the exact versions of the PEM packages
required to allow your package manager to resolve them correctly.

Specify the PEM server and agent version as normal
Then include the full set of PEM packages as `packages` under the instance variables.

```yaml
cluster_vars:
  ...
  pem_server_package_version: '10.2.0-1.bookworm'
  pem_agent_package_version: '10.2.0-1.bookworm'

  ...

  instances:
  ...
  - Name: pemserver
    ...
    vars:
      packages:
        Debian:
          - edb-pem=10.2.0-1.bookworm
          - edb-pem-agent=10.2.0-1.bookworm
          - edb-pem-server=10.2.0-1.bookworm
          - edb-pem-cli=10.2.0-1.bookworm
```

If you require PEM 9, you should also include the docs package.

```yaml
cluster_vars:
  ...
  pem_server_package_version: '9.8.0-1.bookworm'
  pem_agent_package_version: '9.8.0-1.bookworm'

  ...

  instances:
  ...
  - Name: pemserver
    ...
    vars:
      packages:
        Debian:
          - edb-pem=9.8.0-1.bookworm
          - edb-pem-agent=9.8.0-1.bookworm
          - edb-pem-server=9.8.0-1.bookworm
          - edb-pem-cli=9.8.0-1.bookworm
          - edb-pem-docs=9.8.0-1.bookworm
```

## PGD clusters deployed with TPA 23.34 or earlier have primary_slot_name set preventing bdr_init_physical from working (TPA-1229)

### Details
TPA 23.35 resolved an issue where a replication slot name intended for use with EFM would be incorrectly set as the `primary_slot_name` on PGD clusters.
Clusters deployed with TPA 23.35 and above will not have this issue.
However, existing clusters deployed with earlier versions will retain
the incorrect `primary_slot_name` setting, even after deployment run on newer TPA version.

The impact of this incorrect `primary_slot_name` is that if you attempt to add a new node to the cluster (or rebuild a node) using bdr_init_physical, it will hang
on `Waiting for PostgreSQL to accept connections...`, the logs will show a fatal error `replication slot ... does not exist`.

### Workaround
You can manually remove this incorrect setting from each Postgres node in your cluster by deleting the file `/opt/postgres/data/conf.d/8901-primary_slot_name.conf` and reloading Postgres.
As long as you are now using TPA 23.35 or later, it will not be reinstated.