# EDB Postgres Distributed configuration

TPA can install and configure EDB Postgres Distributed (PGD),
formerly known as BDR (Bi-directional replication) versions 3.7, 4.x,
and 5.x.

Access to PGD packages is through EDB's package repositories only.
You must have a valid EDB subscription token to download the packages.

This documentation touches on several aspects of PGD configuration, but 
for an authoritative description of the details,
see the [PGD documentation](https://enterprisedb.com/docs/pgd/latest/).

## How TPA approaches PGD installation

TPA installs PGD and any dependencies on all PGD instances. It also installs Postgres.

After completing the basic Postgres setup and starting Postgres, TPA
then creates `bdr_database` and proceeds to set up a PGD cluster
using the steps that follow.

## Installation

TPA installs the correct PGD packages based on the version
and flavor of Postgres in use (for example, Postgres, Postgres Extended, or
EDB Postgres Advanced Server).

Set `bdr_version` to determine the major version of PGD to install
(that is, 3, 4, or 5). Set `bdr_package_version` to determine the
package to install. For example, use `5.0*` to install the latest 5.0.x package.

## Overview of cluster setup

After installing the required packages, configuring Postgres to load
PGD, and starting the server, TPA sets up PGD nodes,
groups, replication sets, and other resources.

Here's a summary of the steps TPA performs:

* Create a PGD node (using `bdr.create_node()`) for each participating
  instance.

* Create one or more PGD node groups (using `bdr.create_node_group()`)
  based on `bdr_node_groups`.

* Create replication sets, if required, to control the changes that
  are replicated. This decision is based on node group type and memberships. For example,
  subscriber-only and witness nodes might need special handling.
<!-- Check this edit -->
* Join the relevant node groups on the individual instances.

* Perform additional configuration, such as enabling subgroup RAFT or
  proxy routing.

This process involves executing a complex sequence of queries, some on
each instance in turn and others in parallel. To make the steps easier
to follow, TPA designates an arbitrary PGD primary instance as the
`first_bdr_primary` for the cluster and uses this instance to execute
most of these queries. The instance is otherwise not special, and its
identity isn't significant to the PGD configuration.

## Instance roles

Every instance with `bdr` in its role is a PGD instance and
implicitly also a `postgres` server instance.

A PGD instance with `readonly` in its role is a logical standby node
(which joins the PGD node group with `pause_in_standby` set), eligible
for promotion.

A PGD instance with `subscriber-only` in its role is a subscriber-only
node, which receives replicated changes but doesn't publish them.

A PGD instance with `witness` in its role is a witness node.

Each of these PGD instances is implicitly also a `primary`
instance. The exception is an instance with `replica` in its role. That setting
indicates a physical streaming replica of an upstream PGD instance. Such
instances aren't included in any recommended PGD architecture and aren't
currently supported by TPA.

## Configuration settings

The settings that follow are ordinarily set in `cluster_vars`
so that they're set uniformly for all the PGD instances in the cluster.
You can set different values on different instances in some cases, for example,
`bdr_database`. In other cases, though, the result is undefined. For example, all
instances must have exactly the same value of `bdr_node_groups`.

We strongly recommend defining your PGD configuration by setting uniform
values for the whole cluster under `cluster_vars`.

### bdr_database

The `bdr_database` (default: `bdrdb`) is initialized with PGD.

### bdr_node_group

The setting of `bdr_node_group` (default: based on the cluster name)
identifies the PGD cluster for an instance to be a part of. It's also
used to identify a particular cluster for external components, such as
pgd-proxy or harp-proxy.

### bdr_node_groups

This setting is a list of PGD node groups that must be created before the group-join 
stage (if the cluster requires additional subgroups).

In general, `tpaexec configure` generates an appropriate value based
on the selected architecture.

```yaml
cluster_vars:
  bdr_node_groups:
  - name: topgroup
  - name: abc_subgroup
    node_group_type: data
    parent_group_name: topgroup
    options:
      location: abc
  …
```

The first entry must be for the cluster's `bdr_node_group`.

Each subsequent entry in the list must specify a `parent_group_name`
and can optionally specify the `node_group_type` optional.

Each entry can also have an optional key/value mapping of group options.
The available options vary by PGD version.

### bdr_child_group

If `bdr_child_group` is set for an instance (to the name of a group that
is mentioned in `bdr_node_groups`), it joins that group instead of
`bdr_node_group`.

### bdr_commit_scopes

This setting is an optional list of
[commit scopes](https://www.enterprisedb.com/docs/pgd/latest/reference/commit-scopes/)
that must exist in the PGD database (available for PGD 4.1 and later).

```yaml
cluster_vars:
  bdr_commit_scopes:
  - name: somescope
    origin: somegroup
    rule: 'ALL (somegroup) ON received …`
  - name: otherscope
    origin: othergroup
    rule: '…'
  …
```

Each entry must specify a `name` value for the commit scope, the name of the
`origin` group, and a commit scope `rule` value. The groups must correspond
to entries in `bdr_node_groups`.

If you set `bdr_commit_scopes` explicitly, TPA creates, alters, or
drops commit scopes as needed to ensure that the database matches the
configuration. If you don't set it, TPA leaves existing commit
scopes alone.

## Miscellaneous notes

### Hooks

TPA invokes the `bdr-node-pre-creation`, `bdr-post-group-creation`, and
`bdr-pre-group-join` [hooks](tpaexec-hooks.md) during the PGD cluster
setup process.

### Database collations

TPA checks that the PGD database on every instance in a cluster has
the same collation (`LC_COLLATE`) setting. Having different collations in
databases in the same PGD cluster risks data loss.

## Older versions of PGD

TPA no longer actively supports or tests the deployment of BDR v1
(with a patched version of Postgres 9.4), v2 (with Postgres 9.6), or
any PGD versions before v3.7.
