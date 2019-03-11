---
classification: internal
title: HAProxy Cookbook
author:
- Shaun Thomas
- Gianni Ciolli
version: 1.0
copyright-years: 2019
date: 11 March 2019
toc: true
---

\BeginRevisions

\Revision 1.0; 2019-03-11; GC, ST: First version.

\EndRevisions

This document collects several answers on HAProxy that were given to
ACI through support tickets.

# Recipes

In this section we collect some recipes related to HAProxy.

## Administration Socket

In order to send commands to HAProxy, a command administration socket
must be enabled. This corresponds to a section like this in the
`haproxy.cfg` configuration file:

```
global
    stats socket /var/lib/haproxy/stats level admin
```

Once this is set, it becomes possible to send commands to that socket to make 
changes to HAProxy while it is running. Since this syntax is somewhat obscure,
it's usually easier to use the `haproxyctl` utility instead.

### Example

In order to switch to a "backup" node (`node2`) as the new traffic
target, one could issue this command to disable the `node1` server on
backend `be`:

```
sudo haproxyctl disable server be/node1
```

This allows a smooth transition of connections to an alternate backend
without disrupting existing connections. 

PgBouncer 1.9 introduces two settings that can mark a session as in
need of a new backend. These backends won't be reassigned to a new
client frontend and will be terminated right after the current
transaction or session ends.

Once maintenance is complete, the `node1` server on backend `be` can be 
returned to the pool with:

```
sudo haproxyctl enable server be/node1
```

In the reference Always-On architecture, this is the intended use case for
the Master and Shadow Master arrangement.

## Stick Tables

Normally when HAProxy detects a server outage, or is put into
maintenance mode, it will only temporarily redirect traffic to the
designated alternate node.

Once the node reappears, traffic will automatically revert to the
previous target.

This can be prevented by using stick tables, which can be activated in
the `backend` definition as seen here:

```
backend be
    stick-table type ip size 1
    stick on dst
```

These settings create a semi-permanent stick table of one IP address
that points to the current Postgres backend.

If that node disappears, HAProxy will permanently switch to the
alternate node, so that accidental reversion is prevented.

The only way to permanently switch back to the old node once it
reappears is to re-enable it, and then disable the current target to
cause another switch.

## Server Checks

HAProxy detects server state depending on the associated `check`
settings.

BDR nodes are always online, and thus switches can be
immediate. However, to avoid unnecessary and undesired switches, we
recommend using careful judgement when selecting timeouts.

Currently our TPA reference design uses this configuration, which we
have found to ignore most temporary network blips or service restarts:

```
backend be
    option pgsql-check user haproxy

    server node1 node1:5432 maxconn 225 check inter 1500 downinter 6s rise 5 fall 3 
    server node2 node2:5432 maxconn 225 check inter 1500 downinter 6s rise 5 fall 3 backup
```

The meaning of these option is as follows:

- The check is performed every 1500 ms
- The node is considered "down" if it is down for more than 6
  seconds
- The node is considered "up" if 5 checks succeed in a row
- The node is considered "down" if 3 checks fail in a row

With these settings we aim to find a balance between detecting an
outage quickly enough, while moving connections to an alternate node
only when necessary.

## Multiple Backends

Should it be desirable to connect to any node for read balancing
purposes, we suggest creating a separate frontend + backend
configuration.

This would have a read designation and a separate binding port, but
always reach an available backend from the pool.

This for example, would balance between all available servers:

```
frontend fe_ro
    bind 127.0.0.1:5444

    maxconn 1000
    timeout client 1h

    default_backend be_ro

backend be_ro
    option pgsql-check user haproxy
    balance leastconn

    server node1 node1:5432 maxconn 100 check
    server node2 node2:5432 maxconn 100 check
    server node3 node3:5432 maxconn 100 check
    server node4 node4:5432 maxconn 100 check
```

This type of configuration works with any number of physical streaming 
replicas for distributing read load across the cluster.

## Involving PgBouncer

We use PgBouncer to mediate session migration between the Lead and
Shadow Master nodes in our Always-On reference architecture, in
conjunction with HAProxy.

### Example

In this example we wish to migrate from the Master (`node1`) to Shadow
Master (`node2`). We perform these steps from the HAProxy + PgBouncer
node:

```
sudo haproxyctl disable server be/node1
psql -U pgbouncer -p 6432 -h localhost pgbouncer -c 'RECONNECT'
```

THe above commands results in the following behavior:

1. HAProxy starts sending new connections to `node2`
2. All existing connections are marked as needing reconnection by PgBouncer
3. Any ongoing transaction on `node1` will be allowed to complete by PgBouncer
4. Once transaction or session is complete, such marked backends are terminated
5. Any new connection created by PgBouncer will be on `node2`

This change is permanent until `node1` is re-enabled, and the process is 
repeated to move connections back to `node1`.

## Stick Table Peering

HAProxy stick tables work as advertised in the documentation, and
using them is actually very straight-forward.

A previous config shared in this ticket resembled these lines:

```
backend be
    stick-table type ip size 1
    stick on dst
```

To use stick table peering, you'd simply create a list of HAProxy peers, and 
note that in the stick table configuration, like so:

```
peers hapeers
    peer hapxy1 hapxy1:10000
    peer hapxy2 hapxy2:10000

backend be
    stick-table type ip size 1 peer hapeers
    stick on dst
```

Where `hapxy1` and `hapxy2` would be the cnames of the HAProxy nodes. An IP 
address is also acceptable for the `host:port` portion.

### Example

Note that server state is _not_ replicated: if the stick table
changes, and `hapxy1` shows Postgres `node1` is disabled, `hapxy2` may
still show `node1` as enabled.

Even though the stick table will be set to route connections to
`node2`, there's an edge case where `hapxy2` considers `node2` down,
and overrides the stick table.

In this example we show the correct procedure to switch when using
multiple HAProxy nodes, in view of the above considerations:

1. Manually move the stick table using the HAProxy admin socket (assuming backend `be`):

        echo 'set table be key 127.0.0.1 data.server_id 2' | \
            sudo socat /var/lib/haproxy/stats stdio
2. Disable the target server on every HAProxy node with a loop, `tpaexec` command to all HAProxy nodes, or whatever:

        sudo haproxyctl disable server be/node1

That shouldn't be too difficult to automate, but definitely needs to be 
considered when building the procedures.

# Discussion

> For HA reasons we need two HAProxy. What is usually used for HAProxy HA?  
> I've seen keepalived and floating IPs.

I think there might be some confusion here. HAProxy has its own design 
purposes, but in the context of being integrated into a Postgres stack, it 
_is_ the HA solution. When it detects one Postgres node is down, it switches 
to the other.

And that is the real issue you're going to encounter trying to make HAProxy 
itself highly available. Each HAProxy would operate independently. You have 
no guarantee that each HAProxy has made the same decision as to which node(s) 
are online, and where to direct traffic.

In the Always-On document, we explain that there must be a single entrypoint 
into the Primary and Shadow master pair. This is to facilitate maintenance 
and as explained in the previous reply to this ticket, must even be paired 
with PgBouncer to accomplish a smooth transition without interrupting 
transactions in progress.

As the Always-On document also discusses, the second datacenter has its own 
Primary and Shadow master pairs that can substitute for the failure of 
HAProxy or PgBouncer in the first. This is possible because that HAProxy 
points to a completely separate node pairing, and does so _consistently_.

Consider you have this scenario occur in rapid succession:

1. HAProxy A points to node 1
2. HAProxy B points to node 1
3. HAProxy A detects an outage and moves to node 2
4. HAProxy B thinks node 1 is fine and node 2 is down
4. HAProxy A sends traffic to node 2
4. HAProxy A goes down
5. HAProxy... proxy redirects to HAProxy B.
6. Application now has a communication race condition

In a BDR cluster, this scenario won't result in a split brain, but unless 
synchronous replication and CAMO are in place, there's a communication race 
condition where the application may not find the data it expects, as it 
hasn't been sent to the other node yet.

This is one reason we use HAProxy, due to the session affinity. The only way 
to prevent this kind of scenario from replaying is to strictly control the 
sticky tables between the two HAProxy nodes, and then also tightly coordinate 
any floating resource.

But about that floating resource... what will it be? VIPs are notorious for 
sometimes being active on multiple nodes unless STONITH is involved. DNS 
propagates much slower than the accepted failover time HAProxy is capable of 
delivering. Perhaps it's acceptable to stack HAProxy on top of HAProxy? In 
which case the top-level HAProxy itself becomes the failure condition.

I suspect you want to implement something [like
this](https://www.digitalocean.com/community/tutorials/how-to-set-up-highly-available-haproxy-servers-with-keepalived-and-floating-ips-on-ubuntu-14-04).

However, this kind of scenario is designed for an HAProxy setup geared toward 
stateless web applications. In that setup, it doesn't matter where HAProxy 
goes, just so long as it is online.

If this is just so you can implement maintenance on HAProxy or PgBouncer 
nodes, then it's a different discussion. Keepalived or some other daemon set 
up to enforce an online state will lead to the above scenario; manually 
switching a resource won't.

If using a PgBouncer + HAproxy stack, PgBouncer can redirect to any node you 
wish, so replacing the HAProxy node is trivial. Provided there's some code to 
verify the state of the sticky table is consistent, it's even possible to 
automate this. Unfortunately that makes PgBouncer your failure condition 
rather than HAProxy.

So how to swap out the PgBouncer node? Fail over to the other data center 
temporarily. If this is a scenario where there is only one data center, use 
multiple Postgres connection strings with a caveat:

1. Connect to PgBouncer A.
2. If PgBouncer A is unavailable, Postgres will connect to PgBouncer B.
3. PgBouncer B is for maintenance purposes only.

So you'd stand up PgBouncer B specifically so A can be taken offline for 
maintenance, and no other time. If PgBouncer B is always available, there's 
the risk that some application servers will erroneously detect that A is 
down, and communicate with B instead, which may have different end targets. 
Then different parts of the application could be communicating with different 
nodes, which opens up more opportunities for conflicts.

Still, these are all hypothetical scenarios. The important point here is 
strict and consistent control over endpoints. If that can be guaranteed, then 
an HA solution can have multiple HAProxy or PgBouncer nodes. However, that's 
not something we covered in our Always-On document, nor is it something 
handled by TPAexec.

We can possibly explore other options, but all of that is way beyond the 
context of this ticket.

> Do you usually collocate HAProxy and Postgres on the same server (one  
> on each for availability), or collocate them with the app, or you usually  
> have dedicated hosts for HAProxy?

Since PgBouncer and HAProxy go hand-in-hand, we strongly recommend putting 
them on the same host. This host should be an entirely separate node from 
wherever Postgres is installed, simply because it acts as a proxy to 
Postgres. If installed on Postgres node A, and that node goes down, so too 
does the proxy stack.

As with the above scenario, if you have HAProxy on Postgres node A, and also 
on Postgres node B, where is the guarantee that both HAProxy daemons point to 
the same Postgres node?

> With two HAProxy instances, and the sticky table that has state, you need  
> replication. I've read HAProxy can do that. Any quick config?

I'm not sure I understand this question. If you're referring to HAProxy 
stick-table peers, that's not something we've explored at this time. In 
theory, using something like this could solve the above issue regarding 
inconsistent stick tables across multiple nodes.

However, since we haven't explored that functionality, we can make no
recommendations on its feasibility, nor configuration guidelines. We
recommend referring to [the
documentation](http://www.haproxy.org/download/1.9/doc/configuration.txt).

> For failback I understand we need to disable the second node basically.  
> Isn't that a small risk, as in case of an issue with the first node,  
> there is basically no backup from HAProxy point of view. Isn't there a  
> mechanism to simply instruct HAProxy to switch back, without actually  
> disabling the node?

How is this risk any different from the failover process we described? When 
using the HAProxy admin socket to disable a node, it fails over to the 
alternate and updates the stick-table. Once maintenance is complete, the node 
should be re-enabled.

There's still a reciprocal two-node relationship, and a failback is then 
unnecessary unless the other node also requires maintenance. In which case, 
the cluster was returned to normal operation with two enabled nodes. The only 
difference is that Node B is the acting Primary. The failover process is the 
same in all cases.

However, it is also possible to directly manipulate the stick table. This for 
example would force the stick table to point to server 2:

```
echo 'show table be' | \
  sudo socat /var/lib/haproxy/stats stdio

# table: be, type: ip, size:1, used:1
0x2266fa4: key=127.0.0.1 use=0 exp=0 server_id=1

echo 'set table be key 127.0.0.1 data.server_id 2' | \
  sudo socat /var/lib/haproxy/stats stdio

echo 'show table be' | \
  sudo socat /var/lib/haproxy/stats stdio

# table: be, type: ip, size:1, used:1
0x2266fa4: key=127.0.0.1 use=0 exp=0 server_id=2
```

Note this is a much lower-level series of commands than using `haproxyctl`, 
which currently doesn't support manipulating stick tables.

Consider however that stick tables are only advisory. If HAProxy detects and 
feels that Node 2 is down, it will still send traffic to Node 2. Only 
disabling the node will permanently move traffic, as would be expected for 
maintenance purposes.

That is one possible weakness to relying on stick-table replication. There is 
no guarantee that stick tables are honored, as transient outages or network 
connection issues may temporarily override them. And again, that is not 
something we've tested in any case.
