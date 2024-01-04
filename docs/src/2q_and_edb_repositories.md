# How TPA uses 2ndQuadrant and EDB repositories

TPA can download EDB software
(including 2ndQuadrant) from several package sources. The source varies depending on the
selected software, You can configure access to each source.

Special configuration options and
logic for EDB and 2ndQuadrant sources are available. You can add arbitrary
[yum](yum_repositories.md) or [apt](apt_repositories.md) repositories
independently of the logic described here. Likewise, you can [download
packages in advance](tpaexec-download-packages.md)
and add them to a [local repository](local-repo.md) if you prefer.

## Package sources used by TPA

TPA downloads software from three package sources. Each of these
sources provides multiple repositories. In some cases, the same software
is available from more than one source.

 - [EDB Repos 2.0](https://www.enterprisedb.com/repos/)
 - [EDB Repos 1.0](https://www.enterprisedb.com/repos/legacy)
 - [2ndQuadrant Repos](https://techsupport.enterprisedb.com/customer_portal/sw/)

By default, TPA [selects sources and repositories](#how-sources-are-selected-by-default)
based on the architecture and other options you specify. It's
generally not necessary to change these. However, before running `tpaexec deploy`, you must
ensure that you have a valid subscription for all the sources used and
that you [exported the token](#authenticating-with-package-sources). Otherwise, the operation fails.

!!! Note
    EDB is in the process of publishing all software through Repos 2.0,
    and will eventually remove the older repositories.

## Authenticating with package sources

To use [EDB Repos 2.0](https://www.enterprisedb.com/repos/), before you run tpaexec, you must run
`export EDB_SUBSCRIPTION_TOKEN=xxx`. You can get
your subscription token from [the web
interface](https://www.enterprisedb.com/repos-downloads).

To use
[2ndQuadrant repositories](https://techsupport.enterprisedb.com/customer_portal/sw/),
before you run tpaexec, you must run `export TPA_2Q_SUBSCRIPTION_TOKEN=xxx`. 
You can get your subscription token from the 2ndQuadrant
Portal. In the left menu, under **Company info**, select **Company**. Some
repositories are available only by prior arrangement.

To use [EDB Repos 1.0](https://www.enterprisedb.com/repos/legacy), you
must create a text file that contains your access credentials in the
`username:password` format. Before you run tpaexec, run:

```
export EDB_REPO_CREDENTIALS_FILE=/path/to/credentials/file
```

If you don't have an account for any of the sites listed, you can
register for access at the [Account Registration page](https://www.enterprisedb.com/user/register?destination=/repository-access-request).

## How sources are selected by default

If you select the PGD-Always-ON architecture, repositories are
selected from EDB Repos 2.0, and all software is sourced
from these repositories.

If you select the M1 architecture and don't select any proprietary EDB software,
all packages are sourced from PGDG. If you select any proprietary EDB
software, all packages are sourced from EDB Repos 2.0.

For the BDR-Always-ON architecture, the default source is
2ndQuadrant, and the necessary repositories are added from this
source. In addition, the PGDG repositories are used for community
packages, such as PostgreSQL and etcd, as required.
If EDB software that isn't available in the 2ndQuadrant repos is required
(such as EDB Postgres Advanced Server), select repositories from EDB Repos
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

This example configures the `enterprise` and `postgres_distributed`
repositories, giving access to EDB Postgres Advanced Server and PGD5 products.
On Debian or Ubuntu systems, it uses the APT repository. 
RedHat systems use the rpm repositories through the yum front end. 
SLES systems use the rpm repositories through the zypper front end. 

If you specify any EDB repositories, any 2ndQuadrant repositories
specified are ignored and no EDB Repos 1.0 are installed.

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

This example installs the pglogical3 and bdr3 release repositories.
On Debian and Ubuntu systems, it uses the APT repository, and on
RedHat systems, it uses the YUM repository.

The `dl/default/release` repository is always installed by default,
unless you either:

- Explicitly set `tpa_2q_repositories: []`
- Have at least one entry in `edb_repositories`

Either of these action results in no 2ndQuadrant repositories being
installed.
