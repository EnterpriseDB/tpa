# Shipping packages from a local repo

If you create a local repository within your cluster directory, TPAexec
will make any packages in the repository available to cluster instances.
This is an easy way to ship extra packages to your cluster.

Optionally, you can also instruct TPAexec to configure the instances to
use _only_ this repository, i.e., disable all others. In this case, you
must provide _all_ packages required during the deployment, starting
from basic dependencies like rsync, Python, and so on.

## Quickstart

To configure a cluster with a local repo enabled, run:

    tpaexec configure --enable-local-repo …

This will generate your cluster configuration and create a `local-repo`
directory and OS-specific subdirectories. See below for details of the
[recommended layout](#local-repo-layout).

## Disconnected environments

In an environment where the target instances will not have network
access, you can instead configure your cluster with this option:

    tpaexec configure --use-local-repo-only …

This will do everything that `--enable-local-repo` does, and disable the
configuration for all other package repositories. On RedHat instances,
this also includes disabling access to subscription-based services.

In an existing cluster, you can just create the `local-repo` directory
and subdirectories yourself. For a cluster with a local repo enabled
already, you can set `use_local_repo_only: yes` in `config.yml`:

```yaml
cluster_vars:
  use_local_repo_only: yes
```

## Local repo layout

By default, TPAexec will create a `local-repo` directory and OS-specific
subdirectories within it (e.g., `local-repo/Debian/10`), based on the OS
you select for the cluster. We recommend using separate subdirectories
because it makes it easier to accommodate instances running different
distributions.

For example, a cluster running RedHat 8 might have the following layout:

```text
local-repo/
`-- RedHat
    |-- 8.5 -> 8
    `-- 8
        `-- repodata
```

For each instance, TPAexec will look for the following subdirectories of
`local-repo` in order and use the first one it finds:

* `<distribution>/<version>`, e.g., `RedHat/8.5`
* `<distribution>/<major version>`, e.g., `RedHat/8`
* `<distribution>/<release name>`, e.g., `Ubuntu/focal`
* `<distribution>`, e.g., `Debian`
* The `local-repo` directory itself.

If none of these directories exists, of course, TPAexec will not try to
set up any local repo on target instances.

This way, you can put RedHat-specific packages under `RedHat/8` and
Ubuntu-specific packages under `Ubuntu/focal`, and instances will use
the right packages automatically. If you don't have instances running
different distributions, they'll all use the same subdirectory.

## Populating the repository

You must copy packages into the appropriate repository directory and
generate repository metadata before running `tpaexec deploy`.

Note: a future version of TPAexec will include a command that will
download all the packages required for deployment on a disconnected
cluster into the appropriate `local-repo` subdirectory. Until then,

After copying the necessary packages into the repository directory, you
must use an OS-specific tool to generate the repository metadata.

You must generate the metadata on the control node, i.e., the machine
where you run tpaexec. TPAexec will copy the metadata and packages to
target instances.

You must generate the metadata in the subdirectory that the instance
will use, i.e., if you copy packages into `local-repo/Debian/10`, you
must create the metadata in that directory, not in `local-repo/Debian`.

### Debian/Ubuntu repository metadata

For Debian-based distributions, install the `dpkg-dev` package:

```shell
$ sudo apt-get update && sudo apt-get install -y dpkg-dev
```

Now you can use `dpkg-scanpackages` to generate the metadata:

```shell
$ cd local-repo/Debian/buster
# download/copy .deb package files
$ dpkg-scanpackages . | gzip > Packages.gz
```

### RedHat repository metadata

First, install the `createrepo` package:

```shell
$ sudo yum install -y createrepo
```

Now you can use `createrepo` to generate the metadata:

```shell
$ cd local-repo/RedHat/8
# download/copy .rpm package files
$ createrepo .
```

## Copying the repository

TPAexec will use rsync to copy the contents of the repository directory,
including the generated metadata, to a directory on target instances.

If rsync is not already available on an instance, TPAexec can install it
(i.e., `apt-get install rsync` or `yum install rsync`). However, if you
have set `use_local_repo_only`, the rsync package must be included in
the local repo. If required, TPAexec will copy just the rsync package
using scp and install it before copying the rest.

## Repository configuration

After copying the contents of the local repo to target instances,
TPAexec will configure the destination directory as a local (i.e.,
path-based, rather than URL-based) repository.

The idea is that if you provide, say, `example.deb` in the repository
directory, running `apt-get install example` will suffice to install it,
just like any package in any other repository.

## Package installation

TPAexec configures a repository with the contents that you provide, but
if the same package is available from different repositories, it is up
to the package manager to decide which one to install (usually the
latest, unless you specify a particular version).

(However, if you set `use_local_repo_only: yes`, TPAexec will disable
all other package repositories, so that instances can only use the
packages that you provide in `local-repo`.)
