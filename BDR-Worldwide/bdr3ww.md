---
title: "Trusted PostgreSQL Architecture: Postgres-BDR Worldwide\ifdef{USER_MANUAL} User Manual\else Specification\endif"
version: 1.0
customer: 2ndQuadrant
copyright-years: 2018-19
date: 05 July 2019
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

![Database Architecture Diagram\label{ww}](cache/bdr3wwsha.png){ width=85% }

The architecture we propose is displayed in Figure \ref{ww}.

This architecture presents the following characteristics:

- It includes the following nodes:
    - Six BDR 3.6.4 nodes
        - Two nodes located in DC1 (`dc1n1` and `dc1n2`)
        - Two nodes located in DC2 (`dc2n1` and `dc2n2`)
        - Two nodes located in DCDR (`dcdrn1` and `dcdrn2`)
    - Three Barman 2.8 nodes
        - One located in DC1 (`dc1barman`), taking backups from `dc1n1`
        - One located in DC2 (`dc2barman`), taking backups from `dc2n1`
        - One located in DCDR (`dcdrbarman`), taking backups from `dcdrn1` and
          `dcdrn2`. Optionally, this barman server can be split into 2 barman
          servers.
- It is based on the following software:
    - PostgreSQL 11.4
    - pglogical 3.6.4
    - BDR 3.6.4
    - Barman 2.8
- If required, applications may use more than one Master node in the
  same region if data sharding is enabled
- If data sharding is not enabled, applications may use more than one
  Master node in whichever region
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


-- END OF INITIAL EDITING --


# High Availability Procedures

In this section we describe High Availability procedures in more
detail, including failure scenarios as well as maintenance
activities. We cover the following procedures:

- [Swap Lead Master and Shadow Master]
\ifdef{USER_MANUAL}\else- [Node Upgrade]
\endif- [Temporary Master Failure]
- [Permanent Master Failure]
- [Temporary Logical Standby Failure]
- [Permanent Logical Standby Failure]
\ifdef{USER_MANUAL}\else- [Temporary Barman Failure]
- [Permanent Barman Failure]
\endif- [PgBouncer/HAProxy Failure]
- [Temporary Datacenter Failure]
- [Permanent Datacenter Failure]
\ifdef{USER_MANUAL}\else- [Restoring Datacenter Failure Resilience]
\endif

\AuthorComment[GC]{

TODO: We need to add a use case to swap main datacenter, which is only
relevant in the case where the application usage pattern does not
allow simultaneous usage of both Lead Master nodes.

}

Note that we refer to High Availability while accepting a certain
impact on latency, as an expected effect of consistency-focused
options such as CAMO.

This effect is the inevitable result of an intentional trade-off, and
cannot be canceled; users choosing to enable CAMO mode will have to adjust
their expectations accordingly.

## Swap Lead Master and Shadow Master

\ifdef{USER_MANUAL}

This procedure is initiated by the cluster administrators; in this
section we describe it from the point of view of the client.

1. The cluster administrator changes the HAProxy configuration so that
   new connections are directed to Node 2
2. The cluster administrator issues a `RECONNECT` command on
   PgBouncer. The effect on each session is to disconnect both client
   and server at the end of the current transaction (or immediately if
   idle).
3. Each disconnected client tries to reconnect, and is redirected by
   HAProxy to Node 2
4. The administrator issues a `WAIT_CLOSE` command on PgBouncer; when
   this command returns, all the sessions that were not idle when the
   `RECONNECT` was issued have been disconnected, and the swap
   procedure is over.

\AuthorComment[GC]{ Is there a way for the client to detect that a
WAIT CLOSE command is in progress? }

\else

We will only describe the procedure on Datacenter A; the procedure
that applies to Datacenter B is analogous.

1. Set Node 1 to `drain` mode on HAProxy
2. Issue `RECONNECT` on PgBouncer
3. Issue `WAIT_CLOSE` on PgBouncer to wait until all application
   connections have drifted to Node 2

\AuthorComment[GC, TODO]{

Probably this needs rewriting to match our HA tests. Those tests are
being merged to main TPAexec in RM8942, which as of today is blocked
by RM8783.

}

\AuthorComment[GC]{

"Drain" mode for HAProxy means that existing connections are kept and
new ones are redirected away.

FIXME: does "drain" automatically become "down" when all the sticky
connections have been closed?

}

The `RECONNECT` command was specifically designed to cause PgBouncer to
re-establish new connections after existing transactions are complete. Since
HAProxy node migrations are otherwise invisible to PgBouncer, this activates
a transition state that will bridge both the Lead and Shadow systems until
all sessions have committed and cycled.

\endif

![Swap Lead Master and Shadow Master\label{swap}](cache/swap.png){
 width=85% }

The outcome of this procedure is that roles are swapped between the
Lead and Shadow master in the chosen datacenter; the cluster assumes
the state described in Figure \ref{swap}.

\ifdef{USER_MANUAL}\else

PgBouncer is running with `server_fast_close` mode enabled. This means
that the `RELOAD` command sets the `needs_close` flag on all ongoing
client sessions if connection configuration changes are detected. If
these are not made, a `RECONNECT` command is necessary instead.

The effect of the `needs_close` flag is to disconnect any client
session which is in `idle` mode. The expectation is that the
application will try to reconnect right after,
ensuring a faster migration of all the applicative connections to
Node 2.

Note that **no transaction is aborted** as a direct consequence of
this procedure; only idle sessions are terminated.

However, depending on the application model, some ongoing transactions
might be undone to resolve a replication conflict, as explained in the
next section.

\endif

### Conflicts and Latency

The application will try to reconnect right after being disconnected,
ensuring a faster migration of all its connections to Node 2.

In the short time between Step 2 and 3, the application will be
writing at the same time to both Node 1 and Node 2.

With default settings, BDR replicates writes to other nodes only after
commit. This implies that, depending on the application model, there
can be a (usually small) chance of applying incompatible changes to
different nodes.

If this happens, we say that a **Replication Conflict** has occurred.
BDR is able to manage replication conflicts automatically, by applying
a **Conflict Resolution** procedure.

The conflict resolution procedure chooses between the two conflicting
changes in a way which is deterministic and consistent across all
nodes.

By default, BDR chooses the change with the latest timestamp, but the
application developer might want to configure a custom conflict
resolution logic, which must be equally deterministic and consistent
to avoid introducing discrepancies in the cluster.

If the application model does not prevent replication conflicts, then
this possibility must be taken into account. In particular, we
recommend application testing against a set of simulated failures, to
identify which conflicts are likely to occur in each scenario, and
verify that they are resolved in a way that agrees with the
application model.

\ifdef{USER_MANUAL}\else

### Replication Conflicts on Swap

There is a window of opportunity for replication conflicts, as
illustrated by the following example, which features two client
sessions A and B, connected to Node 1 at the start of the Swap
procedure:

1. `RECONNECT` is issued
2. Session A is disconnected by PgBouncer (Session B is not
   disconnected because it's running transaction T2)
3. The application reconnects to Node 2 opening a new Session A', and
   starting transaction T1' again
4. Session A' requests COMMIT of transaction T1' on Node 2; a
   pre-commit message is inserted in Node 2's WAL, and the session
   waits until acknowledgement is received from Node 1
5. Session B requests COMMIT of transaction T2 on Node 1, waiting as
   in Step 4
6. Session A' propagates COMMIT of T1' to Node 1, where it conflicts
   with Session B which is committing T2. Likewise, Session B
   propagates COMMIT of T2 to Node 2, where it conflicts with Session
   A' which is committing T1'. In both cases the conflict is resolved
   by pglogical, using Last Update Wins based on the commit timestamps
   of T1' and T2.

Note that, when CAMO mode is enabled, the commit timestamp of a transaction
is measured when the pre-commit message is inserted in the
WAL. Therefore in Step 6 the conflict is resolved according to
Last-Update-Wins logic based on the "pre-commit" timestamps.

For instance, if T1' and T2 are both inserts, and the pre-commit
message for T1' was emitted after the one for T2, then the INSERT in
T1' is transformed into an UPDATE, producing the same effect as
discarding the INSERT in T2.

In general, BDR handles conflicts automatically;
two conflicting pieces of
information are added to the database, and one of them is given
priority according to a rule which ensures the same outcome on each
node, to avoid desynchronizing the cluster.

It is therefore important that the application takes into account the
possibility of replication conflicts, and that the outcome of the
resolution is in agreement with the application model.

In particular, we recommend application testing against a set of
simulated failures, to identify which conflicts are likely to occur in
this scenario, and plan in advance how to address them.

Conflict caused by the Swap procedure can be prevented by ensuring
that all the existing sessions on Node 1 are disconnected, and that
their transactions have been received by Node 2 and replayed there,
before allowing new transactions to start on Node 2.

This can be done via the following alternate procedure;

1. Change the HAProxy configuration so that new connections are
   directed to Node 2
2. Issue the double PgBouncer command `RECONNECT;PAUSE;`
3. Wait until all transactions on Node 1 have been sent to Node 2, by
   checking the LSN on `pg_stat_replication`
4. Issue `RESUME;` on PgBouncer

Essentially we have added a `PAUSE` / `RESUME` cycle around the
`WAIT_CLOSE` command, and we issue `RECONNECT` and `PAUSE` in the same
statement to ensure that the database is paused before the new
configuration takes effect. The `WAIT_CLOSE` command has been removed,
because all ongoing transactions will have completed, and the
respective client sessions disconnected, when the `PAUSE` command
returns.

\AuthorComment[GC]{

We cannot issue PAUSE before RELOAD or RECONNECT, otherwise the PAUSE will
wait forever.

Is there a (possible) window of opportunity for a session to
disconnect due to the RELOAD and then connect to Node 2 before the
PAUSE is processed?

I don't think so, but if it were, then PgBouncer would need to close
it with a single RELOAD\_PAUSED command, that performs a RELOAD while
setting the "new" database as paused.

}

There is clearly an increase in latency, which we regard as an
unavoidable consequence of the stronger consistency requirement
(cfr. the PACELC Theorem).

\AuthorComment[GC]{

FIXME: add proper PACELC reference

}

\endif

### Multiple HAProxy Instances

Multiple HAProxy nodes can optionally be deployed in the same
datacenter, as described in section [Same-Datacenter Resilience].

Since each HAProxy node changes its configuration based on regular
node health checks, two HAProxy nodes can occasionally be pointing to
different BDR nodes, even if most of the time will be directed to the
same node.

Depending on the application model, this could result in incompatible
changes occasionally applied to different nodes, in a way which is
quite similar to what we already discussed in the [Conflicts and
Latency] section above, to which we refer for the appropriate remedial
actions.

\ifdef{USER_MANUAL}
\else

While this scenario can mostly be countered using techniques such as
Stick Table Peering, it cannot be entirely excluded, as it depends on
the outcome of run-time checks.

As an example, if the HAProxy instances are currently directed to Node
1, as indicated by the stick table, and one of the HAProxy instances
detects failure of Node 1, then that instance will quickly redirect
new connections to Node 2, while the remaining instances will keep
using Node 1.

\endif

### Conflicts in CAMO Mode

CAMO is a feature designed to prevent multiple commits of the same
transactions in certain failure scenarios, by a mechanism in part
similar to Two-Phase Commit (2PC), based on pre-commit notification to
a designated *CAMO partner* node.

It is worth noting that replication conflicts are **equally likely**
when CAMO mode is enabled, because a CAMO pre-commit is quite similar
to a non-CAMO commit with respect to replication conflicts:

- Both travel at the same speed
- The target node cannot roll back the incoming commit
- The timestamp used in conflict resolution is the same (the
  pre-commit timestamp for CAMO pre-commits, and the commit timestamp
  for non-CAMO commits)

\ifdef{USER_MANUAL}\else

#### Example #1

In the following example, T1 and T2 are two conflicting transactions,
performed on different nodes; T2 is performed later and is be aborted:

- Node 1:
	- commit(T1) is requested by Client
	- T1 is pre-committed
- Node 2:
	- commit(T1) is propagated from Node 1
	- T1 is committed
	- commit(T2) is requested by Client
	- T2 is rolled back, being incompatible with T1
- Node 1:
	- commit(T1) is propagated from Node 2
	- T1 is committed

This example is very similar to the following non-CAMO example, and
the outcome is the same:

- Node 1:
	- commit(T1) is requested by Client
	- T1 is committed
- Node 2:
	- commit(T1) is propagated from Node 1
	- T1 is committed
	- commit(T2) is requested by Client
	- T2 is rolled back, being incompatible with T1

#### Example #2

We also provide a negative example where a row-level conflict will
occur despite CAMO mode being enabled:

- Node 1:
	- commit(T1) is requested by Client
	- T1 is pre-committed
- Node 2:
	- commit(T2) is requested by Client
	- T2 is committed
	- commit(T1) is requested by Node 1
	- T1 conflicts with T2
	- the conflict is resolved locally
- Node 1:
	- T2 is propagated from Node 2
	- commit(T1) is propagated from Node 2
	- T1 conflicts with T2
	- the conflict is resolved locally

This example demonstrates a difference between CAMO and Two-Phase
Commit: the CAMO partner node cannot rollback a pre-commit coming from
its CAMO origin, even if it conflicts with a local transaction.

In other words, the only case when the pre-commit of T1 does not
eventually result in a commit is when Node 2 fails permanently before
propagating commit(T1) back to Node 1.

Again, the outcome would be very similar if CAMO mode were not enabled:

- Node 1:
	- commit(T1) is requested by Client
	- T1 is committed
- Node 2:
	- commit(T2) is requested by Client
	- T2 is committed
	- T1 is propagated from Node 1
	- T1 conflicts with T2
	- the conflict is resolved locally
- Node 1:
	- T2 is propagated from Node 2
	- T1 conflicts with T2
	- the conflict is resolved locally

\endif

### Pooling Modes

In this section we describe the three distinct pooling modes that
PgBouncer can adopt:

- Session (the choice for this architecture)
- Transaction
- Statement

Under session mode, PgBouncer is entirely transparent to the
application: when a client session is established, it is assigned to a
server session until when the client session disconnects. Prepared
statements and other session-based settings will work as expected
because they are preserved until disconnection.

Session mode has two main drawbacks:

- The server-side session is assigned to a client session even while
  unused, i.e. when in `idle` state;
- A smooth switchover is not possible: moving an idle client session
  from the old to the new primary transparently would violate session
  mode semantics, because the server session on the new primary would
  clearly be different from the server session on the old primary.

In Transaction mode, PgBouncer only preserves transactions. Precisely,
a server session is assigned only when the client session begins a
transaction, and it may be deassigned when in `idle` state. In
particular, when a client session performs two consecutive
transactions, there is no guarantee that the transactions use the same
server session, and any session state which is outside a transaction
(e.g. prepared statements) can be lost.

On the other hand, transaction mode is not affected by the two issues
mentioned above: an idle client session is not assigned a server
session, and can be moved transparently from one server to another
one, for instance when performing a switchover procedure.

Statement mode extends the behaviour of Transaction mode further, by
forcing a commit and deassigning the server session at the end of a
statement, even without a specific COMMIT statement. We will not
consider this mode in the present document, because it is only for use
in special cases (e.g. PL/Proxy), and does not support multiple
statements in the same transaction.

While in session mode, PgBouncer supports a `RECONNECT` command whose
effect is to disconnect all client sessions without canceling ongoing
transactions: sessions are disconnected immediately, if idle, or at
the end of the current transaction.

Assuming that the client is capable of handling disconnections
correctly (as it should), this command allows a errorless switchover
while preserving session status.

On failover, ongoing transactions will be rolled back, and can
reconnect to PgBouncer. This is usually regarded as an expected and
minimal disruption.

\ifdef{USER_MANUAL}\else

## Node Upgrade

In this section we describe how to perform software or hardware
upgrades on a BDR cluster without interrupting the service.

The BDR software supports rolling upgrades from version 3.5
onwards. This means that it is possible to upgrade one BDR node at the
time, while the remaining BDR nodes are functioning.

This applies to all kinds of upgrades, including:

- Hardware upgrades
- BDR upgrades
- PostgreSQL upgrades
- Upgrade of other software

### Binary Incompatible Upgrades

BDR supports rolling upgrades even if the upgrade is not binary
compatible, e.g. from PostgreSQL 10 to PostgreSQL 11.

However, the upgraded server will no longer produce compatible WAL
files, and will have to be considered by Barman as an entirely
separated server, in a way similar to what noted in the [Reconfiguring
Barman] section below.

\endif

## Temporary Master Failure

In this section we discuss the case when a BDR node fails and then
recovers; the case when a BDR node fails permanently is addressed in
the next section [Permanent Master Failure].

Note that the distinction between temporary and permanent failure is
not entirely formal; certain temporary failures can be considered
permanent if recovery doesn't happen soon enough.

This procedure does not require human intervention as it is entirely
automated; nevertheless, we describe it for documentation and
monitoring purposes, and also because it changes the state of the
cluster.

The procedure is composed by the following steps:

1. Node 1 (the Lead Master) fails temporarily
2. HAProxy notices the failure, and redirects connections towards Node
   2 (the Shadow Master)
3. Node 1 recovers

The outcome of this procedure is to reverse the roles of Lead Master
and Shadow Master, as previously illustrated in Figure \ref{swap}.

### Additional Latency in CAMO Mode

As previously noted, individual commits must be acknowledged by
the CAMO Partner node before being completed.

This means that the master node is subject to higher commit latency,
in exchange for stronger consistency. Also, and more importantly, the
master node **must detect** whether its CAMO Partner node is
unavailable, and in that case **temporarily disable CAMO mode**, to
restore write capability on the surviving node.

Detection of CAMO Partner node failure depends on a number of
parameters, which control keep-alives, timeouts, and how quickly CAMO
mode is restored after the CAMO partner node recovers from a temporary
failure; it is therefore important to tune those parameters in view of
the actual High Availability requirements.

For further details, including the complete list of parameters
relevant to CAMO, we refer to the *Local Mode vs CAMO Mode* section of
the BDR manual.

### Role Reversal and High Availability

We note that the reversal of roles between Lead and Shadow master does
not weaken High Availability, because the [Permanent Master Failure]
section covers failure of Node 1 as well as Node 2, irrespectively of
which node is the Lead Master.

### Replication Conflicts on Temporary Failure

We note that on this scenario incompatible changes could be applied
different nodes, *even if the application always uses only one BDR
node at the time*.

The application must therefore be able to handle this case, similarly
to what discussed in the [Conflicts and Latency] section above.

Consider the following example:

- The application commits transaction T1 on Node 1
- Node 1 fails after T1 commits, but before T1 is transmitted to Node 2
- The application is redirected to Node 2
- The application commits transaction T2 on Node 2
- Node 1 recovers
- Node 1 sends transaction T1 to Node 2
- Transaction T1 conflicts with T2, and BDR resolves the conflict (in
  favour of T2, following Last-Update-Wins)

\ifdef{USER_MANUAL}\else

**Note.** This example is similar to the one described in
[Replication Conflicts on Swap], because a session is moved from Node
1 to Node 2, resulting in incompatible transactions being committed on
those nodes. We refer to that section for more details on replication
conflicts, in particular on the issues that can arise and how
conflicts can be prevented.

\endif

## Permanent Master Failure

Should any master node fail permanently, or not recover quickly
enough, it will have to be replaced with a newly created BDR node.

This procedure is a variant of [Temporary Master Failure], and it
looks very similar from the point of view of the application:

- On the failure of the Lead Master, the application is redirected to
  the Shadow Master
- If the Lead Master recovers in time, the failure is confirmed as
  really "temporary";
- Otherwise, the downtime is too long, and we give up waiting,
  declaring the failure as permanent.

\ifdef{USER_MANUAL}\else

The procedure also differs depending on whether the failed master is
Node 1 or another master node. In this section we discuss the first
case in detail; the other case is simpler, and is addressed with a
similar procedure, with a few changes examined in Section
[Permanent Failure of Other Master].

Let us assume that we are in the configuration described by Figure
\ref{ha} at page \pageref{ha}, and that Node 1 fails. Precisely:

1. Node 1 (the Lead Master) fails
2. HAProxy notices the failure, and redirects traffic towards Node 2

At this point, the cluster is in the state described in Figure
\ref{pmf-1}. In particular:

- Node 2 becomes the Lead Master
- Node 1 becomes the (failed) Shadow Master

![Permanent Master Failure (Swap to Shadow Master)\label{pmf-1}](cache/pmf-1.png){
width=85% }

Now we continue with the following steps:

3. Node 1 is declared "permanently failed"
4. A new BDR node is created in Datacentre A by promoting the logical
   standby Node 5, as shown in Figure \ref{pmf-2}
5. We reconfigure HAProxy, removing Node 1 and adding Node 5.

With Step 5, Node 5 effectively assumes the role of Shadow Master.

If CAMO was configured between Node 1 and Node 2, then it is necessary
to reconfigure CAMO so that Node 5 is the CAMO partner of Node 2, and
vice versa.

\AuthorComment[GC, WIP]{

After discussing with Markus and Petr, it appears that there are
issues in changing the CAMO configuration, and that there is an
interim period while the new CAMO partner could be asked about the
outcome of decisions taken by the old CAMO partner, and give the wrong
answer.

This risk is still unsure as it is being clarified, and is mentioned
here for completeness.

}

6. A new *server* for Node 2 is added to the Barman configuration, as
   specified in Figure \ref{pmf-3}
7. Barman takes the first backup of the server corresponding to Node 2
8. The backup schedule is changed so it performs regular backups of
   Node 2 instead of Node 1
9. A new Node 7 is provisioned, and then it joins the cluster from
   Node 5 as a Logical Standby, using a procedure similar to the one
   described in the [Permanent Logical Standby Failure] scenario

![Permanent Master Failure (Promote Logical
Standby)\label{pmf-2}](cache/pmf-2.png){ width=85% }

![Permanent Master Failure (Reconfigure Barman to use the new Lead
Master)\label{pmf-3}](cache/pmf-3.png){ width=85% }

![Permanent Master Failure (Provision new Logical
Standby)\label{pmf-4}](cache/pmf-4.png){ width=85% }

After this procedure, the failed master (Node 1) is removed, a new
master (Node 5) and a new logical standby (Node 7) have been added, as
described in Figure \ref{pmf-4}.

At this point, the old Lead Master (Node 1) is completely detached
from the cluster. This is appropriate, since a failed node should not
be reused until it is properly inspected, and might have to be
replaced with a newly provisioned node depending on the failure.

### Reconfiguring Barman

In Step 6 of the procedure, we reconfigure Barman adding Node 2 as a
new server, and in Step 7 we take the first backup for that server.

This step includes creating a new replication slot on Node 2, as
specified in the Barman documentation; this is standard procedure on a
PostgreSQL node, designed to avoid loss of WAL data in case of
prolonged disconnection of the Barman node.

We do not try to use Node 2 as a replacement for Node 1, because the
existing WAL and backups from Node 1 will not be compatible with the
new ones from Node 2.

In fact, Barman will consider Node 1 and Node 2 as two entirely
independent servers; backups previously taken from Node 1 will be kept
by Barman as long as specified by its retention policies.

### Permanent Failure of Other Master

When the failed master node is not the source of Barman backups, we
can follow a simpler procedure, because we must not reconfigure
Barman.

The procedure is quite similar, except that steps 6, 7 and 8 must be
skipped, because there is no need to reconfigure Barman.

### Consistent Node-Part

Version 3.1 of BDR introduces a key feature, named *Consistent
Node-Part* which allows the elimination of permanent discrepancies
among the remaining BDR nodes when removing ("parting") a failed node
from a BDR group.

Consistent Node-Part works by leveraging the LSN position reported by
each BDR node. By definition, one node will have the highest LSN from the
parted node of all other nodes in the cluster. This node will use the LSN
values from other nodes to determine which missing transactions to
re-transmit to each. This will allow the cluster to remain consistent
with the most recent acknowledged transaction state corresponding to
the parted node.

\endif

## Temporary Logical Standby Failure

In this section we discuss the case when Node 5 fails and then
recovers.

This scenario will recover automatically and does not need any
operator intervention.

## Permanent Logical Standby Failure

Should a Logical Standby fail permanently, a new node must be
provisioned; until then, the application will be unable to use the
Logical Standby.

This is expected, as the High Availability of this node is not a
requirement of the present architecture.

\ifdef{USER_MANUAL}\else

The newly provisioned node must join the cluster from Node 2 as a
Logical Standby; for this it is sufficient to follow the default
procedure specified in the BDR manual.

## Temporary Barman Failure

In this section we discuss the case when the Barman node fails and
then recovers; the case when the Barman node fails permanently is
addressed in the next section [Permanent Barman Failure].

As noted in Section [Temporary Master Failure] above, the distinction
between temporary and permanent failure is not entirely formal;
certain temporary failures can be considered permanent if recovery
does not happen within an acceptable time limit.

Barman uses a replication slot to ensure that no WAL is lost on
temporary failures, meaning that WAL is accumulated on the sending
node when the Barman node is down. This means that a prolonged Barman
downtime affects the sending node: it should considered
permanent, and therefore addressed as described in Section
[Permanent Barman Failure].

Conversely, as soon as the Barman node recovers, the cluster
automatically goes back to the original state, without needing any
human intervention. This makes this scenario actually simpler than
[Temporary Master Failure].

## Permanent Barman Failure

If the Barman node fails to recover, we must carry out the following
procedure:

1. Isolate the failed Barman node in order to ensure that it does not
   connect again
2. Provision a new Barman node
	a. In addition to the standard Barman configuration, the
       replication slot must be reset to the current position, using
       the `--reset` option of the `barman receive-wal` command. This
       is because the replication slot exists already and is pointing
       to the location reached by the previous Barman server
3. Take a backup to verify that the configuration is functioning

The other nodes will not be affected.

### Barman Redundancy {#br-pbf}

Strictly speaking, the new Barman node will not initially provide the
desired recovery window.

However, the Barman node in the other datacenter will have a similar
recovery window on Node 3.

This is generally sufficient for addressing most Point-In-Time
Recovery scenarios, considering that Node 3 is eventually consistent
with Node 1.

\endif

## PgBouncer/HAProxy Failure

The two PgBouncer/HAProxy nodes represent two independent *entry
points* to the BDR cluster, one for each datacenter.

Since the BDR cluster is multi-master, the application can
indifferently use either entry point. In particular, if one entry
point fails, then the application can just use the other one, without
having to perform any cluster-level procedure, as specified in Figure
\ref{ha-epf}.

![PgBouncer/HAProxy Node Failure\label{ha-epf}](cache/epf.png){
 width=85% }

Note that different entry points give access to nodes in different
datacenters.

This means that conflicting queries will result in replication
conflicts, as mentioned in the [Conflicts and Latency] section.

If the application model can avoid replication conflicts, or handle
them without excessive strain, then the application can be made
resilient to datacenter failure by simply using a "client failover"
syntax that supports the specification of multiple hosts and ports.

Examples of client failover syntax include JDBC, and LibPQ:

* <https://www.postgresql.org/docs/11/static/libpq-connect.html#LIBPQ-MULTIPLE-HOSTS>

For instance, when using LibPQ to specify a sequence of multiple entry
points, the application will react to connection failure by trying all
entry points in sequence until one of them succeeds.

### Same-Datacenter Resilience

The above procedure implies that HAProxy is a single point of failure
within each datacenter; this might not be desirable, for instance in
single-datacenter installation, or when the opposite datacenter should
be left only to appropriate emergencies due to latency or financial
considerations.

The introduction of a second PgBouncer/HAProxy node in each
datacenter, configured to use the same pair of BDR nodes as the
existing one, provides same-datacenter resilience; see Figure
\ref{2ep}.

![Two PgBouncer/HAProxy nodes for each
datacentre\label{2ep}](cache/2ep.png){ width=85% }

\ifdef{USER_MANUAL}\else

#### Stick Tables

The role of HAProxy is to react quickly to BDR node failure by
redirecting connections to the other node. However, if the failed node
recovers, then HAProxy automatically reverts back to it, which is not
an ideal behaviour because it involves two redirections for each
temporary failure.

The solution is to configure a *stick table* which prevents the second
redirection; or, in other words, it ensures that HAProxy "sticks" to
the outcome of the first redirection. An example stick table
configuration is as follows:

```
backend be
  stick-table type ip size 1
  stick on dst
```

#### Peering

When multiple HAProxy instances are using the same set of BDR servers,
we can use *peering* to ensure that the stick tables are kept aligned,
by adding a `peer` section to the stick table definition, and defining
a group of HAProxy nodes that are "peers":

```
peers hapeers
  peer hapxy1 hapxy1:10000
  peer hapxy2 hapxy2:10000

backend be
  stick-table type ip size 1 peer hapeers
  stick on dst
```

We note the following points:

- Peering does not result in immediate and blocking synchronization of
  the stick tables: the window of opportunity for row-level conflicts
  still exists, albeit smaller
- The likeliness of row-level conflicts is not affected by CAMO, as
  explained in the [Conflicts in CAMO Mode] section

#### Switchover Procedure

Peering synchronizes stick table state, not server state; if HAProxy
detects the failure of the node indicated in the stick table, then it
will redirect connections to the other node.

Based on that, we provide an example of the correct procedure for
switching from Node 1 to Node 2:

1. Manually switch the IP in the stick table to Node 2 (this requires using the
   HAProxy administration socket):
```
set table be key 127.0.0.1 data.server_id 2
```

1. Disable Node 1 by running the following command on **both** HAProxy nodes:
```
sudo haproxyctl disable server be/node1
```

\endif

## Temporary Datacenter Failure

A temporary datacenter failure does not interrupt regular operations
nor node swap, because each datacenter has one entry point as well as
two BDR nodes.

However, DDL operations are suspended during the failure, as the
required quorum cannot be reached due to the simultaneous failure of
two BDR nodes.

## Permanent Datacenter Failure

If a whole datacenter fails, then the only remaining option is failing over
to the other datacenter. As both datacenters are fully active, the
application itself is also likely to be writing at both locations.

If a datacenter is fully lost, the application will also be inoperable
in the lost location. This is usually acceptable, because the
application is still be operating in the remaining datacenter,
providing service continuity.

\ifdef{USER_MANUAL}\else

A full datacenter failover is recommended even if the datacenter loss
is only partial, but still significant. For instance, if multiple
database servers, or some other critical component of the stack, are
lost. The reason is that these situations are sufficiently complicated
to require careful analysis and manual intervention, such as
recovering transactions committed but not fully propagated due to the
failure.

This example shows how to activate Datacenter B in the case of total
loss of Datacenter A:

1. Verify that Datacenter A is failed, and that Datacenter B is
   functioning
2. Redirect the application towards Datacenter B
3. Connect to Node 3 in Datacenter B, and part Node 1 and Node 2 from
   BDR replication using the `bdr.part_node()` function with
   `force := true`
4. Repeat the previous step on Node 4

The reason for Step 4 is that `force := true` makes the
`bdr.part_node()` function execute only locally. This allows parting
nodes when quorum is not available, but at the same time requires that
we repeat the parting commands on each remaining node.

After this procedure, applications are reconfigured to use Datacenter
B, as Figure \ref{dc-failure} shows.

![Datacenter Failure\label{dc-failure}](cache/dcf.png){ width=85% }

The procedure just described is able to restore operations after a
datacenter failure. However, the resulting cluster does not have full
redundancy capabilities, because it is vulnerable to a second
Datacentre loss.

This risk must therefore be addressed at the earliest opportunity by
provisioning new nodes in another functioning datacenter, as described
in [Restoring Datacenter Failure Resilience].

## Restoring Datacenter Failure Resilience

After a permanent datacenter failure as described in the previous
section, we must restore appropriate resilience by provisioning new
database nodes in a new, functioning datacenter.

The starting point for the following procedure is the architecture
described in Figure \ref{dc-failure}.

As in the [Permanent Failure of Other Master] section, to which we
refer for further details, we have two equivalent ways to carry out
the procedure of adding a new node to an existing cluster.

In the following steps we will only include generic mentions of that
procedure, because the choice is better left to the reader.

1. Configure a new BDR node (Node 1') in Datacenter C, and add it to
   the BDR cluster, either via Node 3 or via Node 4
2. Configure a second BDR node (Node 2') in Datacenter C, and add it
   to the BDR cluster via Node 1'

Once the two BDR nodes have been created, the remaining nodes are
provisioned from scratch exactly like a new installation:

3. Configure a PgBouncer/HAProxy node, directed to the newly created
   Nodes 1' and 2'
4. Optionally, configure a second PgBouncer/HAProxy node, depending on
   how many PgBouncer/HAProxy nodes are required
5. Configure a new Barman node to take backups from the newly created
   Node 1'
6. A new node joins from the newly created Node 2' as a Logical
   Standby

\endif
