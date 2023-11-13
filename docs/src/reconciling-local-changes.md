# Reconciling changes made outside of TPA
Any changes made to a TPA created cluster that are not performed by
changing the TPA configuration will not be saved in `config.yml`. This
means that your cluster will have changes that the TPA configuration
won't be able to recreate.

This page shows how configuration is managed with TPA and the preferred
ways to make configuration changes. We then look at strategies to make,
and reconcile, the results of making manual changes to the cluster.

## Why might I need to make manual configuration changes?
The most common scenario in which you may need to make configuration
changes outside of TPA is if the operation you are performing is not
supported by TPA. The two most common such operations are destructive
changes, such as removing a node, and upgrading the major version of
Postgres.

### Destructive changes
In general TPA will not remove previously deployed elements of a
cluster, even if these are removed from `config.yml`. This sometimes
surprises people because a strictly declarative system should always
mutate the deployed artifacts to match the declaration. However, making
destructive changes to production database can have serious consequences
so it is something we have chosen not to support.

### Major-version Postgres upgrades
TPA does not yet provide an automated mechanism for performing major
version upgrades of Postgres. Therefore if you need to perform an
in-place upgrade on an existing cluster this must be performed using
other tools such as pg_upgrade or [bdr_pg_upgrade](https://www.enterprisedb.com/docs/pgd/latest/upgrades/bdr_pg_upgrade/#bdr_pg_upgrade-command-line).

## What can happen if changes are not reconciled?
A general issue with unreconciled changes is that if you deploy a new
cluster using your existing `config.yml`, or provide your `config.yml` to
EDB Support in order to reproduce a problem, it will not match the
original cluster. In addition, there is potential for operational
problems should you wish to use TPA to manage that cluster in future.

The operational impact of unreconciled changes varies depending on the
nature of the changes. In particular whether the change is destructive,
and whether the change blocks TPA from running by causing an error or
invalidating the data in `config.yml`.

### Non-destructive, non-blocking changes
Additive changes are often accommodated with no immediate operational
issues. Consider manually adding a user. The new user will continue to
exist and cause no issues with TPA at all. You may prefer to manage the
user through TPA in which case you can declare it in `config.yml` but
the existence of a manually-added user will cause no operational issues.

Some manual additions can have more nuanced effects. Take the example of
an extension which has been manually added. Because TPA does not make
destructive changes, the extension will not be removed when `tpaexec
deploy` is next run. **However**, if you made any changes to the
Postgres configuration to accommodate the new extension these may be
overwritten if you did not make them using one of TPA's supported
mechanisms (see below).

Furthermore, TPA will not make any attempt to modify the `config.yml`
file to reflect manual changes and the new extension will be omitted
from `tpaexec upgrade` which could lead to incompatible software
versions existing on the cluster.


### Destructive, non-blocking changes
Destructive changes that are easily detected and do not block TPA's
operation will simply be undone when `tpaexec deploy` is next run.
Consider manually removing an extension. From the perspective of TPA,
this situation is indistinguishable from the user adding an extension to
the `config.yml` file and running deploy. As such, TPA will add the
extension such that the cluster and the `config.yml` are reconciled,
albeit in the opposite way to that the user intended.

Similarly, changes made manually to configuration parameters will be
undone unless they are:

1. Made in the `conf.d/9999-override.conf` file reserved for manual
   edits;
2. Made using `ALTER SYSTEM` SQL; or
3. Made [natively in TPA](#postgres_conf_settings) by adding
   `postgres_conf_settings`.

Other than the fact that option 3 is self-documenting and portable,
there is no pressing operational reason to reconcile changes made by
method 1 or 2.

### Destructive, blocking changes
Changes which create a more fundamental mismatch between `config.yml`
can block TPA from performing operations. For example if you physically
remove a node in a bare metal cluster, attempts by TPA to connect to
that node will fail, meaning most TPA operations will exit with an error
and you will be unable to manage the cluster with TPA until you
reconcile this difference. 

## How to reconcile configuration changes
In general, the reconciliation process involves modifying `config.yml`
such that it describes the current state of the cluster and then running
`tpaexec deploy`.

### Example: parting a PGD node
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

  select * from bdr.part_node('node-2');

Rerun `deploy`. Note that, whilst no errors occur, the node is still
parted. This can be verified using the command `pgd show-nodes` on any
of the nodes. This is because TPA will not overwrite the metadata which
tells PGD the node is parted. 

!!! Note 
It is not possible to reconcile the `config.yml` with this cluster state
because TPA, and indeed PGD itself, has no mechanism to initiate a node
in the 'parted' state. In principle you could continue to use TPA to
continue this parted cluster, but this is not advisable. In most cases
you will wish to continue to fully remove the node and reconcile
`config.yaml`.
!!!

### Example: removing a PGD node completely
The previous example parted a node from the PGD cluster, but left the
node itself intact and still managed by TPA in a viable but
unreconcilable state. 

To completely decommission the node, it is safe to simply turn off the
server corresponding to `node-2`. If you attempt to run `deploy` at this
stage, it will fail early when it cannot reach the server. 

To reconcile this change in `config.yml` simply delete the entry under
`instances` corresponding to `node-2`. It will look something like this:

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

You can now manage this node as usual using TPA. However, the original
cluster still has metadata that refers to `node-2` so to complete
reconciliation it is recommended to run the following SQL on each node
to remove the metadata. *This step is essential if you wish to add a
node of the same name in future.*

```sql
select * from bdr.drop_node('node-2');
```

!!! Note 
If you wish to join the original `node-2` back to the cluster after
removing it in this way, you can do so simply by restoring the deleted
lines of `config.yml` but you must ensure that `select * from
bdr.drop_node('node-2');` has been run on this node and that the PGDATA
directory has been deleted.
!!!

### Example: changing the superuser password
TPA automatically generates a password for the superuser which you may
view using `tpaexec show-password <cluster> <superuser-name>`. If you
change the password manually (for example using the `/password` command
in psql) you will find that after `tpaexec deploy` is next run, the
password has reverted to the one set by TPA. To make the change through
TPA, and therefore make it persist across runs of `tpaexec deploy`, you
must use the command `tpaexec store-password <cluster> <superuser-name>`
to specify the password, then run `tpaexec deploy`. This also applies to
any other user created through TPA.

### Example: adding or removing an extension
A simple single-node cluster can be deployed with the following
`config.yml`.

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
You may manually add the pgvector extension by connecting to the node
and running `apt install postgresql-15-pgvector` then executing the
following SQL command: `CREATE EXTENSION vector;`. This will not cause
any operational issues, beyond the fact that `config.yml` no longer
describes the cluster as fully as it did previously. However, it is
advisable to reconcile `config.yml` (or indeed simply use TPA to add the
extension in the first place) by adding the following cluster variables. 

```yaml
cluster_vars:
  ...  
  extra_postgres_packages:
   common:
   - postgresql-15-pgvector
  postgres_extensions:
  - vector
  ```

After adding this configuration, you may manually remove the extension
by executing the SQL command `DROP EXTENSION vector;` and then 
`apt remove postgresql-15-pgvector`. However if you run `tpaexec deploy`
again without reconciling `config.yml`, the extension will be
reinstalled. To reconcile `config.yml`, simply remove the lines added
previously.

!!! Note 
As noted previously, TPA will not honour destructive changes.
So simply removing the lines from `config.yml` will not remove the
extension. It is necessary to perform this operation manually then
reconcile the change.
!!!