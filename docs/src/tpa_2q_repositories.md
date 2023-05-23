# Configuring 2ndQuadrant repositories

This page explains how to configure 2ndQuadrant package repositories on
any system.

For more details on the EDB and 2ndQuadrant package sources used by
TPA see [this page](2q_and_edb_repositories.md).

To specify the complete list of 2ndQuadrant repositories to install on
each instance in addition to the 2ndQuadrant public repository, set
`tpa_2q_repositories` to a list of 2ndQuadrant repository names:

```yaml
cluster_vars:
  tpa_2q_repositories:
    - products/pglogical3/release
    - products/bdr3/release
```

This example will install the pglogical3 and bdr3 release repositories.
On Debian and Ubuntu systems, it will use the APT repository, and on
RedHat systems, it will use the YUM repository. The 2ndQuadrant
repositories are not available for SLES systems.

To use
[2ndQuadrant repositories](https://techsupport.enterprisedb.com/customer_portal/sw/),
you must `export TPA_2Q_SUBSCRIPTION_TOKEN=xxx` before you run
tpaexec. You can get your subscription token from the 2ndQuadrant
Portal, under "Company info" in the left menu, then "Company". Some
repositories are available only by prior arrangement.

The `dl/default/release` repository is always installed by default,
unless you

- explicitly set `tpa_2q_repositories: []`, or
- have at least one entry in `edb_repositories`.

Either or the above will result in no 2ndQuadrant repositories being installed.
