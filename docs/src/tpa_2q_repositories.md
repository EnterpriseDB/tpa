# Configuring 2ndQuadrant repositories

You can configure 2ndQuadrant package repositories on
any supported system.

For more details on the EDB and 2ndQuadrant package sources used by
TPA, see [How TPA uses 2ndQuadrant and EDB repositories](2q_and_edb_repositories.md).

To specify the complete list of 2ndQuadrant repositories to install on
each instance in addition to the 2ndQuadrant public repository, set
`tpa_2q_repositories` to a list of 2ndQuadrant repository names:

```yaml
cluster_vars:
  tpa_2q_repositories:
    - products/pglogical3/release
    - products/bdr3/release
```

This example installs the pglogical3 and bdr3 release repositories.
On Debian and Ubuntu systems, it uses the APT repository, and on
RedHat systems, it uses the YUM repository. The 2ndQuadrant
repositories aren't available for SLES systems.

To use
[2ndQuadrant repositories](https://techsupport.enterprisedb.com/customer_portal/sw/),
you must run `export TPA_2Q_SUBSCRIPTION_TOKEN=xxx` before you run
tpaexec. You can get your subscription token from the 2ndQuadrant
Portal. In the left menu, select **Company info > Company**. Some
repositories are available only by prior arrangement.

The `dl/default/release` repository is always installed by default,
unless you either:

- Explicitly set `tpa_2q_repositories: []`
- Have at least one entry in `edb_repositories`

As a result of either of these actions, no 2ndQuadrant repositories is installed.
