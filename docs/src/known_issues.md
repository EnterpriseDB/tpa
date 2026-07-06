---
description: Known issues in TPA and their workarounds.
---

# Known issues

This page lists known issues affecting the current version of TPA.
Where one is known, a workaround for each issue is provided.

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

## SSH configuration templating error in clusters using  `forward_ssh_agent: true`

### Details

TPA 23.43 changed the templating for the ssh_config file in the cluster
directory and introduced a bug whereby if `forward_ssh_agent` is set to
True, the generated config file will be invalid. The default for this
setting is False, and it is usually only set to True when installing
components of the cluster from source code for testing.

### Workaround
After running `tpaexec provision` to generate the ssh_config file, edit
the file in a text editor. Find the line reading `IdentitiesOnly yes
ForwardAgent yes`, usually line 7 in the file, and split it two lines by
adding a newline after the first "yes". The file will be overwritten by
`tpaexec provision` so it must be re-edited after provisioning when a
change is made to config.yml.

## PEM agent registration options provided by `pemagent_registration_opts` are not reflected in `agent.cfg` and therefore do not take effect (TPA-1376)

### Details

The `pemagent_registration_opts` option is used to pass additional
command line options to the pemworker utility during PEM agent
registration. Some of these options affect the immediate act of
registration, some affect the data written to the PEM database, and
others affect the content of the generated `agent.cfg` file which is
used to determine agent behaviour. In TPA's current implementation, the
`agent.cfg` file is overwritten immediately after registration with a
templated version, meaning any changes made to this file as a result of
`pemagent_registration_opts` are lost.

### Workaround

Avoid using `pemagent_registration_opts` unless you are sure the options
you specify do not interact with `agent.cfg`. Apply any changes required
to `agent.cfg` using a post-deploy hook.