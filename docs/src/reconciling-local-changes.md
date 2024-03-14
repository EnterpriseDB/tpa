# Reconciling changes made outside of TPA
Any changes made to a TPA-created cluster that aren't performed by
changing the TPA configuration aren't saved in `config.yml`. This
means that your cluster can have changes that the TPA configuration
can't re-create.

You can manage the configuration with TPA, using the preferred
ways to make configuration changes described here. You can also use the 
strategies we recommend to make,
and reconcile, the results of making manual changes to the cluster.

## Why might I need to make manual configuration changes?
The most common scenario in which you might need to make configuration
changes outside of TPA is if the operation you're performing isn't
supported by TPA. The two most common such operations are destructive
changes, such as removing a node, and upgrading the major version of
Postgres.

### Destructive changes
In general, TPA doesn't remove previously deployed elements of a
cluster, even if these are removed from `config.yml`. This behavior sometimes
surprises people because a strictly declarative system should always
mutate the deployed artifacts to match the declaration. However, making
destructive changes to a production database can have serious consequences,
so it's something we've chosen not to support.

### Major-version Postgres upgrades
TPA doesn't yet provide an automated mechanism for performing major
version upgrades of Postgres. Therefore, if you need to perform an
in-place upgrade on an existing cluster, you need to do so using
other tools, such as pg_upgrade or [bdr_pg_upgrade](https://www.enterprisedb.com/docs/pgd/latest/upgrades/bdr_pg_upgrade/#bdr_pg_upgrade-command-line).

## What can happen if changes aren't reconciled?
A general issue with unreconciled changes is that if you deploy a new
cluster using your existing `config.yml` or provide your `config.yml` to
EDB Support to reproduce a problem, it doesn't match the
original cluster. In addition, there's potential for operational
problems if you want to use TPA to manage that cluster in future.

The operational impact of unreconciled changes varies depending on the
nature of the changes, in particular, whether the change is destructive
and whether the change blocks TPA from running by causing an error or
invalidating the data in `config.yml`.

### Nondestructive, non-blocking changes
Additive changes are often accommodated with no immediate operational
issues. Consider manually adding a user. The new user continues to
exist and cause no issues with TPA. You might prefer to manage the
user through TPA, in which case you can declare it in `config.yml`. But
the existence of a manually added user doesn't cause operational issues.

Some manual additions can have more nuanced effects. Take the example of
an extension that was manually added. Because TPA doesn't make
destructive changes, the extension isn't removed when `tpaexec
deploy` next runs. However, if you made any changes to the
Postgres configuration to accommodate the new extension, these might be
overwritten if you didn't make them using one of TPA's supported
mechanisms (see [Destructive, non-blocking changes](#destructive-non-blocking-changes) 
and [Destructive, blocking changes](#destructive-blocking-changes).

Furthermore, TPA doesn't make any attempt to modify the `config.yml`
file to reflect manual changes. The new extension is omitted
from `tpaexec upgrade`, which can lead to incompatible software
versions existing on the cluster.


### Destructive, non-blocking changes
Destructive changes that are easily detected and don't block TPA's
operation are undone when `tpaexec deploy` next runs.
Consider manually removing an extension. From the perspective of TPA,
this situation is indistinguishable from adding an extension to
the `config.yml` file and running `deploy`. As such, TPA adds the
extension such that the cluster and the `config.yml` are reconciled,
albeit in the opposite way to that was intended.

Similarly, changes made manually to configuration parameters are
undone unless they're made either:

- In the `conf.d/9999-override.conf` file reserved for manual
   edits
- Using `ALTER SYSTEM` SQL
- [Natively in TPA](postgresql.conf.md#postgres_conf_settings) by adding
   `postgres_conf_settings`

Other than the fact making the changes natively in TPA is self-documenting and portable,
there's no pressing operational reason to reconcile changes made by
either of the other methods.

### Destructive, blocking changes
Changes that create a more fundamental mismatch between `config.yml`
can block TPA from performing operations. For example, if you physically
remove a node in a bare-metal cluster, attempts by TPA to connect to
that node will fail, meaning most TPA operations will exit with an error.
You can't manage the cluster with TPA until you
reconcile this difference. 

## How to reconcile configuration changes
In general, the reconciliation process involves modifying `config.yml`,
such that it describes the current state of the cluster, and then running
`tpaexec deploy`.

### Example: Parting a PGD node
Deploy a minimal PGD cluster using the bare architecture and a configure
command such as:

```bash
tpaexec configure mycluster \
-a PGD-Always-ON \
--platform bare \
--edbpge 15 \
--location-names a \
--pgd-proxy-routing local
```

Part a node using this SQL, which can be executed from any node:

```
  select * from bdr.part_node('node-2');
```

Rerun `deploy`. While no errors occur, the node is still
parted. You can verify this using the command `pgd show-nodes` on any
of the nodes. This is because TPA doesn't overwrite the metadata that
tells PGD the node is parted. 

!!! Note 
It isn't possible to reconcile the `config.yml` with this cluster state
because TPA, and PGD itself, has no mechanism to initiate a node
in the "parted" state. In principle, you can continue to use TPA to
continue this parted cluster, but we don't recommend this. In most cases,
you'll want to continue to fully remove the node and reconcile
`config.yaml`.
!!!

### Example: Removing a PGD node completely
The previous example parted a node from the PGD cluster but left the
node intact and still managed by TPA in a viable but
unreconcilable state.

To completely decommission the node, it's safe to turn off the
server corresponding to `node-2`. If you attempt to run `deploy` at this
stage, it will fail early when it can't reach the server. 

To reconcile this change in `config.yml`, delete the entry under
`instances` corresponding to `node-2`. It looks something like this:

```yaml
- Name: node-2
  public_ip: 44.201.93.236
  private_ip: 172.31.71.186
  location: a
  node: 2
  role:
  - bdr
  - pgd-proxy
  vars:
    bdr_child_group: a_subgroup
    bdr_node_options:
      route_priority: 100
```


!!! Note
If you wish to join the original `node-2` back to the cluster after
having removed it from `config.yml`, you can do so by restoring the
deleted lines of `config.yml`, stopping Postgres, deleting the
`PGDATA` directory on that node, and then repeating `tpaexec
deploy`. As noted above, TPA will not remove an existing database,
even if the corresponding entry is deleted from `config.yml`, so you
need to perform this action manually.
!!!

### Example: Changing the superuser password
TPA generates a password for the superuser that you can
view using `tpaexec show-password <cluster> <superuser-name>`. If you
change the password manually (for example using the `/password` command
in psql), after `tpaexec deploy` next runs, the
password reverts to the one set by TPA. To make the change through
TPA, and therefore make it persist across runs of `tpaexec deploy`, you
must use the command `tpaexec store-password <cluster> <superuser-name>`
to specify the password, and then run `tpaexec deploy`. This requirement also applies to
any other user created through TPA.

### Example: adding or removing an extension
You can deploy a simple single-node cluster with the following
`config.yml`:

```yaml
---
architecture: M1
cluster_name: singlenode

cluster_vars:
  postgres_flavour: postgresql
  postgres_version: '15'
  preferred_python_version: python3
  tpa_2q_repositories: []

instance_defaults:
  image: tpa/debian:11
  platform: docker
  vars:
    ansible_user: root

instances:
- Name: nodeone
  node: 1
  role:
  - primary
```
You can manually add the pgvector extension by connecting to the node
and running `apt install postgresql-15-pgvector`. Then execute the
following SQL command: `CREATE EXTENSION vector;`. This doesn't cause
any operational issues beyond the fact that `config.yml` no longer
describes the cluster as fully as it did previously. However, we
recommend reconciling `config.yml` (or using TPA to add the
extension in the first place) by adding the following cluster variables:

```yaml
cluster_vars:
  ...  
  extra_postgres_packages:
   common:
   - postgresql-15-pgvector
  extra_postgres_extensions:
  - vector
  ```

After adding this configuration, you can manually remove the extension
by executing the SQL command `DROP EXTENSION vector;` and then 
`apt remove postgresql-15-pgvector`. However, if you run `tpaexec deploy`
again without reconciling `config.yml`, the extension is
reinstalled. To reconcile `config.yml`, remove the lines added
previously.

!!! Note 
As noted previously, TPA doesn't honor destructive changes.
So removing the lines from `config.yml` doesn't remove the
extension. You need to perform this operation manually and then
reconcile the change.
!!!