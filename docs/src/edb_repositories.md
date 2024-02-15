# Configuring EDB Repos 2.0 repositories

You can configure EDB Repos 2.0 package repositories using cluster variables.

For more details on the EDB and 2ndQuadrant package sources used by
TPA, see [How TPA uses 2ndQuadrant and EDB repositories](2q_and_edb_repositories.md).

To specify the complete list of repositories from EDB Repos 2.0 to
install on each instance, set `edb_repositories` to a list of EDB
repository names:

```yaml
cluster_vars:
  edb_repositories:
    - enterprise
    - postgres_distributed
```

This example installs the enterprise subscription repository as well
as postgres_distributed, giving access to EDB Postgres Advanced Server and PGD version 5 products.
On Debian or Ubuntu systems, it uses the apt repository. On
RedHat or SLES systems, it uses the rpm repositories, through the yum
or zypper front ends, respectively.

If you specify any EDB repositories, any 2ndQuadrant repositories
specified are ignored and no EDB Repos 1.0 are installed.

To use [EDB Repos 2.0](https://www.enterprisedb.com/repos/), you must
`export EDB_SUBSCRIPTION_TOKEN=xxx` before you run tpaexec. You can get
your subscription token from [the web
interface](https://www.enterprisedb.com/repos-downloads).
