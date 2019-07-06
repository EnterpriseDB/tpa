---
title: "Trusted PostgreSQL Architecture: Postgres-BDR Worldwide\ifdef{USER_MANUAL} User Manual\else Specification\endif"
version: 1.0
customer: 2ndQuadrant
copyright-years: 2018-19
date: 5 July 2019
author: 2ndQuadrant
table-row-colors: false
toc: true
classification: partner-confidential
display-author-comments:\ifdef{DEBUG} true\else false\endif
display-revision-history: false
header-includes: \usepackage{cprotect}
---

\BeginRevisions

\Revision 1.0; 2019-07-05; GC, WI: First version.

\EndRevisions

# Introduction

\ifdef{USER_MANUAL}

This document describes the behaviour of
BDR-Worldwide, a flexible architecture based on version 3.6.4
of Postgres-BDR,
from the viewpoint of the application developer.

\else

This document provides the technical specification of
BDR-Worldwide, a flexible architecture based on version 3.6.4
of Postgres-BDR.

\endif

The primary goal of this architecture is to provide data redundancy across
multiple different geographic region, and the data can be distributed across
the BDR nodes through *replication*, *fragmentation* (sharding) or a combination
of both.

\AuthorComment[GC]{

Barman Geo-Redundancy does not seem suitable for this architecture.

While in principle it could be applied, we must consider the usage
limitations of physical backups as explained in the [Backups Usage
Limitations] section.

Because of this, it seems preferable to have a higher degree of
symmetry, with each Barman instance independently taking backups from
a node in the same datacenter.

}

## Database Architecture

![Database Architecture Diagram\label{ww}](cache/main.png){ width=85% }

The architecture we propose is displayed in Figure \ref{ww}.

This architecture presents the following characteristics:

- It includes the following nodes:
    - Six BDR 3.6.4 nodes (nodes 1 - 6)
        - Two nodes located in datacenter A (nodes 1 and 2)
        - Two nodes located in datacenter B (nodes 3 and 4)
        - Two nodes located in datacenter DR (nodes 5 and 6)
    - Three Barman 2.8 nodes
        - One located in datacenter A, taking backups from node 1
        - One located in datacenter B, taking backups from node 3
        - One located in datacenter DR, taking backups from nodes 5
          and 6. Optionally, this server can be split into 2
          barman servers.
- It is based on the following software:
    - 2ndQuadrant PostgreSQL 11.4 r1.6
    - pglogical 3.6.4
    - BDR 3.6.4
    - Barman 2.8
- Reference data is replicated across all the BDR nodes
- The data is divided in two shards:
	- The first shard is replicated across nodes 1, 2 and 5
	- The second shard is replicated across nodes 3, 4 and 6
- Applications may use more than one Master node at the time, in the
  same shard, if the usage pattern allows it (e.g. if they are able to
  separate reads from writes, or if their write patterns avoid
  conflicts)
- If a BDR node fails, the application can simply point to the other
  Master node in the same region
\ifdef{USER_MANUAL}\else
- Each Barman node is initially configured to take backups and WAL
  from one of the Master nodes located in the same region
- Each Barman node receives WAL via *Physical Streaming Replication*
  (PSR)
- Each Barman nodes uses a replication slot, to ensure that it
  receives all the WAL records before they are eliminated on the
  upstream node
\endif

\ifdef{USER_MANUAL}\else

## Backups with Barman

The data in the BDR cluster is backed up using Barman; there are three
Barman instances, initially configured to use one of the Master nodes
in the same datacenter as a source for backups and WAL.

For the Disaster Recovery Data Center (DCDR), the Barman server is
initially configured to use both Master nodes located in the same
datacentre as a source for backups and WAL.

During the life cycle of the cluster, in regions DC1 and DC2, the Master
node which the Barman server is configure to take backups from, can fail.
In this case, applications will failover to the other Master node in the
same datacentre. The Barman server in the same datacentre can also be
pointed to this other Master node, and a new backup can be taken.

However, when possible we will keep using the same source for Barman,
due to some limitations documented in section [Backup Usage
Limitations] below.

### Backup Usage Limitations

Two different BDR nodes are physically incompatible, meaning e.g. that
WAL files and backups coming from Node `dc1n2` cannot be seamlessly merged
with the existing WAL files and backups previously collected by Barman
from Node `dc1n1`.

Because of this, there are some limitations in how a physical backup
of a BDR node can be used, and precisely:

- If the backup is **physically compatible** with one of the current
  BDR nodes in the cluster:
    - It is **possible** to use the backup to add a physical standby
	  to that BDR node;
    - It is **possible** to use the backup to add a new BDR node to
	  the cluster, using the `bdr_init_physical` utility pointed to
	  the physically compatible BDR node.
- Otherwise:
	- It is **not possible** to use the backup to add a physical
	  standby to the BDR node which is physically compatible;
	- It is **not possible** to use the backup to add a new node to
	  the cluster.
- In any case:
	- The backup can be used to **restore a separate node**, e.g. for
	  the purpose of extracting data to be fed back into the BDR
	  cluster via one of the existing nodes, or as the first node of a
	  new BDR cluster.
