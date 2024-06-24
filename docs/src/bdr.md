---
description: How to configure and deploy EDB Postgres Distributed (PGD) with TPA.
---

# EDB Postgres Distributed configuration

TPA can install and configure EDB Postgres Distributed (PGD),
formerly known as BDR (Bi-directional replication) versions 3.7, 4.x,
and 5.x.

Access to PGD packages is through EDB's package repositories only.
You must have a valid EDB subscription token to download the packages.

This documentation touches on several aspects of PGD configuration, but
we refer you to the [PGD
documentation](https://enterprisedb.com/docs/pgd/latest/) for an
authoritative description of the details.

## Introduction

TPA will install PGD and any dependencies on all PGD instances along
with Postgres itself.

After completing the basic Postgres setup and starting Postgres, TPA
will then create the `bdr_database` and proceed to set up a PGD cluster
through the various steps described below.

## Installation

TPA will install the correct PGD packages, depending on the version
and flavour of Postgres in use (e.g., Postgres, Postgres Extended, or
EPAS).

Set `bdr_version` to determine which major version of PGD to install
(i.e., 3, 4, 5). Set `bdr_package_version` to determine which exact
package to install (e.g., '5.0*' to install the latest 5.0.x).

## Overview of cluster setup

After installing the required packages, configuring Postgres to load
PGD, and starting the server, TPA will go on to set up PGD nodes,
groups, replication sets, and other resources.

Here's a summary of the steps TPA performs:

* Create a PGD node (using bdr.create_node()) for each participating
  instance

* Create one or more PGD node groups (using bdr.create_node_group())
  depending on `bdr_node_groups`

* Create replication sets, if required, to control exactly which changes
  are replicated (depending on node group type and memberships, e.g.,
  subscriber-only and witness nodes may need special handling)

* Join the relevant node groups on the individual instances

* Perform additional configuration, such as enabling subgroup RAFT or
  proxy routing.

(This process involves executing a complex sequence of queries, some on
each instance in turn, and others in parallel. To make the steps easier
to follow, TPA designates an arbitrary PGD primary instance as the
"first_bdr_primary" for the cluster, and uses this instance to execute
most of these queries. The instance is otherwise not special, and its
identity is not significant to the PGD configuration itself.)

## Instance roles

Every instance with `bdr` in its `role` is a PGD instance, and
implicitly also a `postgres` server instance.

A PGD instance with `readonly` in its role is a logical standby node
(which joins the PGD node group with `pause_in_standby` set), eligible
for promotion.

A PGD instance with `subscriber-only` in its role is a subscriber-only
node, which receives replicated changes but does not publish them.

A PGD instance with `witness` in its role is a witness node.

Every PGD instance described above is implicitly also a `primary`
instance. The exception is an instance with `replica` in its role; that
indicates a physical streaming replica of an upstream PGD instance. Such
instances are not included in any recommended PGD architecture, and not
currently supported by TPA.

## Configuration settings

The settings mentioned below should ordinarily be set in `cluster_vars`,
so that they are set uniformly for all the PGD instances in the cluster.
You can set different values on different instances in some cases (e.g.,
`bdr_database`), but in other cases, the result is undefined (e.g., all
instances must have exactly the same value of `bdr_node_groups`).

We strongly recommend defining your PGD configuration by setting uniform
values for the whole cluster under `cluster_vars`.

### bdr_database

The `bdr_database` (default: bdrdb) will be initialised with PGD.

### bdr_node_group

The setting of `bdr_node_group` (default: based on the cluster name)
identifies which PGD cluster an instance should be a part of. It is also
used to identify a particular cluster for external components (e.g.,
pgd-proxy or harp-proxy).

### bdr_node_groups

This is a list of PGD node groups that must be created before the group
join stage (if the cluster requires additional subgroups).

In general, `tpaexec configure` will generate an appropriate value based
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

Each subsequent entry in the list must specify a `parent_group_name`,
and may specify the `node_group_type` (optional).

Each entry may also have an optional key/value mapping of group options.
The available options vary by PGD version.

### bdr_child_group

If `bdr_child_group` is set for an instance (to the name of a group that
is mentioned in `bdr_node_groups`), it will join that group instead of
`bdr_node_group`.

### bdr_commit_scopes

This is an optional list of
[commit scopes](https://www.enterprisedb.com/docs/pgd/latest/reference/commit-scopes/)
that must exist in the PGD database (available for PGD 4.1 and above).

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

Each entry must specify the `name` of the commit scope, the name of the
`origin` group, and the commit scope `rule`. The groups must correspond
to entries in `bdr_node_groups`.

If you set `bdr_commit_scopes` explicitly, TPA will create, alter, or
drop commit scopes as needed to ensure that the database matches the
configuration. If you do not set it, it will leave existing commit
scopes alone.

## Miscellaneous notes

### Hooks

TPA invokes the bdr-node-pre-creation, bdr-post-group-creation, and
bdr-pre-group-join [hooks](tpaexec-hooks.md) during the PGD cluster
setup process.

### Database collations

TPA checks that the PGD database on every instance in a cluster has
the same collation (LC_COLLATE) setting. Having different collations in
databases in the same PGD cluster is a data loss risk.

## Older versions of PGD

TPA no longer actively supports or tests the deployment of BDR v1
(with a patched version of Postgres 9.4), v2 (with Postgres 9.6), or
any PGD versions below v3.7.
