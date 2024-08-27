---
description: How to configure EDB Repos 2.0 package repositories.
---

# Configuring EDB Repos 2.0 repositories

TPA sources EDB software from 
[EDB Repos 2.0](https://www.enterprisedb.com/repos/). 
To use EDB Repos 2.0 you must `export EDB_SUBSCRIPTION_TOKEN=xxx` 
before you run tpaexec.
You can get your subscription token from 
[the web interface](https://www.enterprisedb.com/repos-downloads).

!!! Note
If you create your `config.yml` file using the `tpaexec configure`
command, the `edb_repositories` key will be automatically populated with
the necessary repositories for your selected configuration, so you 
shouldn't need to edit it.
!!! 

To specify the complete list of repositories from EDB Repos 2.0 to
install on each instance, set `edb_repositories` to a list of EDB
repository names:

```yaml
cluster_vars:
  edb_repositories:
    - enterprise
    - postgres_distributed
```

This example will install the 'enterprise' subscription repository as 
well as 'postgres_distributed' giving access to EPAS and PGD products.
On Debian or Ubuntu systems, it will use the APT repository and on
RedHat or SLES systems, it will use the rpm repositories, through the yum
or zypper frontends respectively.