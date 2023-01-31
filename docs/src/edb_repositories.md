# Configuring EDB repositories

This page explains how to configure EDB package repositories on
any system.

Set `edb_repositories` to a list of EDB repository names:

```yaml
cluster_vars:
  edb_repositories:
    - enterprise
    - postgres_distributed
```

This example will install enterprise subscription repository as well as
postgres_distributed giving access to EPAS and BDR4+ products.
On Debian and Ubuntu systems, it will use the APT repository, and on
RedHat systems, it will use the YUM repository.

To use
[EDB Repositories](https://cloudsmith.io/~enterprisedb/repos/)
you must `export EDB_SUBSCRIPTION_TOKEN=xxx` before you run
tpaexec. You can get your subscription token from the cloudsmith web interface,
under any repository page you have access to, on left menu "Entitlement Tokens".
