# Configuring EDB Repos 2.0 repositories

This page explains how to configure EDB Repos 2.0 package repositories
on any system.

For more details on the EDB and 2ndQuadrant package sources used by
TPA see [this page](2q_and_edb_repositories.md).

To specify the complete list of repositories from EDB Repos 2.0 to
install on each instance, set `edb_repositories` to a list of EDB
repository names:

```yaml
cluster_vars:
  edb_repositories:
    - enterprise
    - postgres_distributed
```

This example will install the enterprise subscription repository as well
as postgres_distributed giving access to EPAS and PGD5 products.
On Debian or Ubuntu systems, it will use the APT repository and on
RedHat or SLES systems, it will use the rpm repositories, through the yum
or zypper frontends respectively.

If any EDB repositories are specified, any 2ndQuadrant repositories
specified will be ignored and no EDB Repos 1.0 will be installed.

To use [EDB Repos 2.0](https://www.enterprisedb.com/repos/) you must
`export EDB_SUBSCRIPTION_TOKEN=xxx` before you run tpaexec. You can get
your subscription token from [the web
interface](https://www.enterprisedb.com/repos-downloads).
