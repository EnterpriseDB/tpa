# TPAexec rolling updates

The `tpaexec update-postgres` command performs a minor-version update
of Postgres and related packages without interrupting overall cluster
operations. Individual instances will be stopped and restarted during
the update, but queries will be routed in such a way as to allow
applications to continue database operations.

The exact procedure is architecture-specific.

## BDR-Always-ON

For BDR clusters, the update process goes through the cluster instances
one by one and does the following:

1. Tell haproxy the server is under maintenance.
2. If the instance was the active server, request pgbouncer to reconnect
   and wait for active sessions to be closed.
3. Stop Postgres, update packages, and restart Postgres.
5. Finally, mark the server as "ready" again to receive requests through
   haproxy.

BDR logical standby or physical replica instances are updated without
any haproxy or pgbouncer interaction. Non-Postgres instances in the
cluster are left alone.

You can control the order in which the cluster's instances are updated
by defining the `update_hosts` variable:

```
$ tpaexec update-postgres ~/clusters/speedy \
  -e update_hosts=quirk,keeper,quaver
```

This may be useful to minimise lead/shadow switchovers during the update
by listing the active BDR primary instances last, so that the shadow
servers are updated first.

If your environment requires additional actions, the
[postgres-pre-update and postgres-post-update hooks](tpaexec-hooks.md)
allow you to execute custom Ansible tasks before and after the package
installation step.

## M1

For M1 clusters, `update-postgres` will first update the streaming
replicas one by one, then perform a [switchover](tpaexec-switchover.md)
from the primary to one of the replicas, update the primary, and
switchover back to it again.

## Package version selection

By default, `tpaexec update-postgres` will update to the latest
available versions of the installed packages if you did not explicitly
specify any package versions (e.g., Postgres, BDR, or pglogical) when
you created the cluster.

If you did select specific versions, for example by using any of the
`--xxx-package-version` options (e.g., postgres, bdr, pglogical) to
[`tpaexec configure`](tpaexec-configure.md), or by defining
`xxx_package_version` variables in config.yml, the update will do
nothing because the installed packages already satisfy the requested
versions.

In this case, you must edit config.yml, remove the version settings, and
re-run `tpaexec provision`. The update will then install the latest
available packages. You can still update to a specific version by
specifying versions on the command line as shown below:

```
$ tpaexec update-postgres ~/clusters/speedy -vv         \
  -e postgres_package_version="2:11.6r2ndq1.6.13*"      \
  -e pglogical_package_version="2:3.6.11*"              \
  -e bdr_package_version="2:3.6.11*"
```

Please note that version syntax here depends on your OS distribution and
package manager. In particular, yum accepts `*xyz*` wildcards, while
apt only understands `xyz*` (as in the example above).

It is your responsibility to ensure that the combination of Postgres,
BDR, and pglogical package versions that you request are sensible. That
is, they should work together, and there should be an upgrade path from
what you have installed to the new versions.

For BDR clusters, it is a good idea to explicitly specify exact versions
for all three components (Postgres, BDR, pglogical) rather than rely on
the package manager's dependency resolution to select the correct
dependencies.

We strongly recommend testing the update in a QA environment before
running it in production.

## Known issues

Please note that the use of wildcards in `*_package_version` is not
supported when added permanently to `config.yml`. Unexpected updates to
installed software can occur during `tpaexec deploy` operations. For
example, if the value for `bdr_package_version` was set to `3.6.*` then
ansible would not be able to match this to an installed version of bdr,
and it would attempt to install the latest version available of the same
package name, e.g. 3.7.

We are aware of this limitation as an ansible bug and will address
this in a future release of TPAexec.
