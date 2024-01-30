# Creating and using a local repository

If you create a local repository in your cluster directory, TPA
makes any packages in the repository available to cluster instances.
This provides an easy way to ship extra packages to your cluster.

Optionally, you can also instruct TPA to configure the instances to
use _only_ this repository, disabling all others. In this case, you
must provide _all_ packages required during the deployment, starting
from basic dependencies like rsync, Python, and so on.

You can create a local repository manually or have TPA create one for
you.

!!! Note
    Specific instructions are available for [managing clusters in an
    air-gapped](air-gapped.md) environment.

## Creating a local repository with TPA

TPA includes tools to help create such a local repository. Specifically
you can use the `--enable-local-repo` switch with `tpaexec configure` to
create an empty directory structure to use as a local repository.
Use `tpaexec download-packages` to populate that structure with the
necessary packages.

### Creating the directory structure

To configure a cluster with a local repository, run:

    `tpaexec configure --enable-local-repo …`

This command generates your cluster configuration and creates a `local-repo`
directory and OS-specific subdirectories. See [Local repo layout](#local-repo-layout)
for details.

### Populate the repository and generate metadata

Run [`tpaexec download-packages`](tpaexec-download-packages.md) to
download all the packages required by a cluster into the local-repo.
The resulting repository contains the full dependency tree of all
packages so the entire cluster can be installed from this repository.
Metadata for the repository is also created, which means
it's ready to use immediately.

## Creating a local repository manually

## Local repo layout

To create a local repository manually, you must first create an
appropriate directory structure. When using `--enable-local-repo`,
TPA creates a `local-repo` directory and OS-specific
subdirectories within it (for example, `local-repo/Debian/10`), based on the OS
you select for the cluster. We recommend that you also use this structure
for repositories you create manually.

For example, a cluster running RedHat 8 might have the following layout:

```text
local-repo/
`-- RedHat
    |-- 8.5 -> 8
    `-- 8
        `-- repodata
```

For each instance, TPA looks for the following subdirectories of
`local-repo` in order and uses the first one it finds:

* `<distribution>/<version>`, e.g., `RedHat/8.5`
* `<distribution>/<major version>`, e.g., `RedHat/8`
* `<distribution>/<release name>`, e.g., `Ubuntu/focal`
* `<distribution>`, e.g., `Debian`
* The `local-repo` directory itself.

If none of these directories exists, TPA doesn't try to
set up any local repository on target instances.

## Populating the repository and generating metadata

You must complete the steps that follow before running
`tpaexec deploy`.

To populate the repository, copy the packages you want to include into
the appropriate directory. Then generate metadata using the correct
tool for your system, as follows.

!!! Note
    You must generate the metadata on the control node, that is, the machine
    where you run tpaexec. TPA copies the metadata and packages to
    target instances.

!!! Note
    You must generate the metadata in the subdirectory that the instance
    will use. That is, if you copy packages into `local-repo/Debian/10`, you
    must create the metadata in that directory, not in `local-repo/Debian`.

### Debian/Ubuntu repository metadata

For Debian-based distributions, install the `dpkg-dev` package:

```shell
$ sudo apt-get update && sudo apt-get install -y dpkg-dev
```

Use `dpkg-scanpackages` to generate the metadata:

```shell
$ cd local-repo/Debian/buster
# download/copy .deb package files
$ dpkg-scanpackages . | gzip > Packages.gz
```

### RedHat/SLES repository metadata

First, install the `createrepo` package:

```shell
$ sudo yum install -y createrepo
```

Use `createrepo` to generate the metadata:

```shell
$ cd local-repo/RedHat/8
# download/copy .rpm package files
$ createrepo .
```

## How TPA uses the local repository

### Copying the repository

TPA uses rsync to copy the contents of the repository directory
to a directory on target instances. The contents include the generated metadata.

If rsync isn't already available on an instance, TPA can install it
(that is, `apt-get install rsync` or `yum install rsync`). However, if you
have set `use_local_repo_only`, the rsync package must be included in
the local repo. If required, TPA copies just the rsync package
using scp and installs it before copying the rest.

### Repository configuration

After copying the contents of the local repo to target instances,
TPA configures the destination directory as a local repository,
that is, path based, rather than URL based.

If you provide, say, `example.deb` in the repository
directory, running `apt-get install example` is enough to install it,
just like any package in any other repository.

### Package installation

TPA configures a repository with the contents that you provide. But
if the same package is available from different repositories, it's up
to the package manager to decide which one to install. Usually it installs the
latest, unless you specify a particular version.

However, if you set `use_local_repo_only: yes`, TPA disables
all other package repositories, so that instances can use only the
packages that you provide in `local-repo`.
