# Reconciling changes made outside of TPA

In general, if a cluster was created using TPA it is advisable to manage
configuration changes to that cluster using TPA. This page is designed
to help users understand how TPA manages configuration, what the
implications of making local changes to a TPA-managed cluster are, and
how to reconcile such changes.

## What constitutes a configuration change?
*This definition seems questionable with changes which wouldn't normally
appear in the config at all, like inserting some data into a table*
Consider a cluster, 'A'. Now imagine a change is applied to it and call
the resulting cluster 'B'. If the config.yml required to deploy a fresh
cluster identical to 'A' is different to the config.yml required to
deploy a cluster identical to 'B' then the change you made is a
configuration change.

## Are there configuration changes which cannot be performed using TPA?
Yes, there are changes which would meet the above definition that cannot
be implemented by TPA. The most notable class of such changes is
*destructive changes*. In general TPA will not remove previously
deployed elements of a cluster, even if these are removed from the
config.yml. This sometimes surprises people because a strictly
declarative system should always mutate the deployed artifacts to match
the declaration. However, making destructive change to production
database can have serious consequences so it is something we have chosen
not to support.

## What can happen if changes are not reconciled?
A general issue with unreconciled changes is that if you deploy a new
cluster using your existing config.yml, or provide your config.yml to
EDB Support in order to reproduce a problem, it will not match the
original cluster. In addition, there is potential for operational
problems should you wish to use TPA to manage that cluster in future.

The operational impact of unreconciled changes varies depending on the
nature of the changes. In particular whether the change is destructive,
and whether the change blocks TPA from.

### Non-destructive, non-blocking changes
Additive changes that can be detected by TPA by inspecting the cluster
are often accommodated with no operational issues, Consider manually
adding an extension. Because TPA does not make destructive changes, the
extension will not be removed when `tpaexec deploy` is next run.
Furthermore, because TPA inspects the cluster prior to making changes,
`tpaexec upgrade` will successfully upgrade the new extension despite it
being absent from the config.yml.

It should be noted however that, even when such a change is detected,
TPA will not make any attempt to modify the config.yml file.

### Destructive, non-blocking changes
Destructive changes that are easily detected and do not block TPA's
operation will simply be undone when `tpaexec deploy` is next run.
Consider manually removing an extension. From the perspective of TPA,
this situation is indistinguishable from the user adding an extension to
the config.yml file and running deploy. As such, TPA will add the
extension such that the cluster and the config.yml are reconciled, albeit
in the opposite way to that the user intended.

### Destructive, blocking changes
Changes which create a more fundamental mismatch between config.yml can
block TPA from performing operations. For example if you physically
remove a node in a bare metal cluster, attempts by TPA to connect to
that node will fail, meaning most TPA operations will exit with an error
and you will be unable to manage the cluster with TPA until you
reconcile this difference.

### Non-destructive, blocking changes
Changes do not have to be destructive to be blocking... 
changing the superuser password? Or would TPA just change it back using local auth?

## How to reconcile configuration changes
In general, the reconciliation process involves modifying config.yml
such that it describes the current state of the cluster and then running
`tpaexec deploy` to verify that it can run, and ?is there another reason?

### Example: removing a node

### Example: adding an extension
An M1 cluster 

