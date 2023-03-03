# How TPA uses 2ndQuadrant and EDB repositories

This page explains the package sources from which TPA can download EDB
(including 2ndQuadrant) software, how the source varies depending on the
selected software, and how to configure access to each source.

Note that this page only describes the special configuration options and
logic for EDB and 2ndQuadrant sources. Arbitrary
[yum](yum_repositories.md) or [apt](apt_repositories.md) repositories
can be added independently of the logic described here. Likewise,
packages can be [downloaded in advance](tpaexec-download-packages.md)
and added to a [local repository](local-repo.md) if preferred.

## Package sources used by TPA

TPA downloads software from three package sources. Each of these
sources provides multiple repositories. In some cases, the same software
is available from more than one source.

 - [EDB Repos 2.0](https://www.enterprisedb.com/repos/)
 - [EDB Repos 1.0](https://www.enterprisedb.com/repos/legacy)
 - [2ndQuadrant Repos](https://techsupport.enterprisedb.com/customer_portal/sw/)

By default, TPA will [select sources and repositories automatically](#how-sources-are-selected-by-default)
based on the architecture and other options you have specified, so it is
not generally necessary to change these. However, you will need to
ensure that you have a valid subscription for all the sources used and
that you have [exported the token](#authenticating-with-package-sources)
before running `tpaexec deploy` or the operation will fail.

!!! Note
    EDB is in the process of publishing all software through Repos 2.0,
    and will eventually remove the older repositories.

## Authenticating with package sources

To use [EDB Repos 2.0](https://www.enterprisedb.com/repos/) you must
`export EDB_SUBSCRIPTION_TOKEN=xxx` before you run tpaexec. You can get
your subscription token from [the web
interface](https://www.enterprisedb.com/repos-downloads).

To use
[2ndQuadrant repositories](https://techsupport.enterprisedb.com/customer_portal/sw/),
you must `export TPA_2Q_SUBSCRIPTION_TOKEN=xxx` before you run
tpaexec. You can get your subscription token from the 2ndQuadrant
Portal, under "Company info" in the left menu, then "Company". Some
repositories are available only by prior arrangement.

To use [EDB Repos 1.0](https://www.enterprisedb.com/repos/legacy) you
must create a text file that contains your access credentials in the
`username:password` format and run `export
EDB_REPO_CREDENTIALS_FILE=/path/to/credentials/file` before you run
tpaexec.

If you do not have an account for any of the sites listed, you can
register for access at
https://www.enterprisedb.com/user/register?destination=/repository-access-request

## How sources are selected by default

If the PGD-Always-ON architecture is selected, repositories will be
selected from EDB Repos 2.0 and all software will be sourced
from these repositories.

For M1 and BDR-Always-ON architectures, the default source is
2ndQuadrant, and the necessary repositories will be added from this
source. In addition, the PGDG repositories will be used for community
packages such as PostgreSQL and etcd as required.
If EDB software not available in the 2ndQuadrant repos is required
(e.g. EDB Advanced Server), repositories will be selected from EDB Repos
1.0.

## Specifying EDB 2.0 repositories

To specify the complete list of repositories from EDB Repos 2.0 to
install on each instance, set `edb_repositories` to a list of EDB
repository names:

```yaml
cluster_vars:
  edb_repositories:
    - enterprise
    - postgres_distributed
```

This example will configure the `enterprise` and `postgres_distributed`
repositories, giving access to EPAS and PGD5 products.
On Debian and Ubuntu systems, it will use the APT repository, and on
RedHat systems, it will use the YUM repository.

If any EDB repositories are specified, any 2ndQuadrant repositories
specified will be ignored and no EDB Repos 1.0 will be installed.

## Specifying 2ndQuadrant repositories

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
RedHat systems, it will use the YUM repository.

The `dl/default/release` repository is always installed by default,
unless you

- explicitly set `tpa_2q_repositories: []`, or
- have at least one entry in `edb_repositories`.

Either or the above will result in no 2ndQuadrant repositories being
installed.

