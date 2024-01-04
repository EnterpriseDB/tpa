# Creating and using a local repository

If you create a local repository within your cluster directory, TPA
will make any packages in the repository available to cluster instances.
This is an easy way to ship extra packages to your cluster.

Optionally, you can also instruct TPA to configure the instances to
use _only_ this repository, i.e., disable all others. In this case, you
must provide _all_ packages required during the deployment, starting
from basic dependencies like rsync, Python, and so on.
f
You can create a local repository manually, or have TPA create one for
you. Instructions for both are included below.

!!! Note
    Specific instructions are available for [managing clusters in an
    air-gapped](air-gapped.md) environment.

## Creating a local repository with TPA

TPA includes tools to help create such a local repository. Specifically
the `--enable-local-repo` switch can be used with `tpaexec configure` to
create an empty directory structure to be used as a local repository,
and `tpaexec download-packages` populates that structure with the
necessary packages.

### Creating the directory structure

To configure a cluster with a local repository, run:

    tpaexec configure --enable-local-repo …

This will generate your cluster configuration and create a `local-repo`
directory and OS-specific subdirectories. See below for [details of the
layout](#local-repo-layout).

### Populate the repository and generate metadata

Run [`tpaexec download-packages`](tpaexec-download-packages.md) to
download all the packages required by a cluster into the local-repo.
The resulting repository will contain the full dependency tree of all
packages so the entire cluster can be installed from this repository.
Metadata for the repository will also be created automatically meaning
it is ready to use immediately.

## Creating a local repository manually

## Local repo layout

To create a local repository manually, you must first create an
appropriate directory structure. When using `--enable-local-repo`,
TPA will create a `local-repo` directory and OS-specific
subdirectories within it (e.g., `local-repo/Debian/10`), based on the OS
you select for the cluster. We recommend that this structure is also
used for manually created repositories.

For example, a cluster running RedHat 8 might have the following layout:

```text
local-repo/
`-- RedHat
    |-- 8.5 -> 8
    `-- 8
        `-- repodata
```

For each instance, TPA will look for the following subdirectories of
`local-repo` in order and use the first one it finds:

* `<distribution>/<version>`, e.g., `RedHat/8.5`
* `<distribution>/<major version>`, e.g., `RedHat/8`
* `<distribution>/<release name>`, e.g., `Ubuntu/focal`
* `<distribution>`, e.g., `Debian`
* The `local-repo` directory itself.

If none of these directories exists, of course, TPA will not try to
set up any local repository on target instances.

## Populating the repository and generating metadata

The steps detailed below must be completed before running
`tpaexec deploy`.

To populate the repository, copy the packages you wish to include into
the appropriate directory. Then generate metadata using the correct
tool for your system as detailed below.

!!! Note
    You must generate the metadata on the control node, i.e., the machine
    where you run tpaexec. TPA will copy the metadata and packages to
    target instances.

!!! Note
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

### RedHat/SLES repository metadata

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

## How TPA uses the local repository

### Copying the repository

TPA will use rsync to copy the contents of the repository directory,
including the generated metadata, to a directory on target instances.

If rsync is not already available on an instance, TPA can install it
(i.e., `apt-get install rsync` or `yum install rsync`). However, if you
have set `use_local_repo_only`, the rsync package must be included in
the local repo. If required, TPA will copy just the rsync package
using scp and install it before copying the rest.

### Repository configuration

After copying the contents of the local repo to target instances,
TPA will configure the destination directory as a local (i.e.,
path-based, rather than URL-based) repository.

If you provide, say, `example.deb` in the repository
directory, running `apt-get install example` will suffice to install it,
just like any package in any other repository.

### Package installation

TPA configures a repository with the contents that you provide, but
if the same package is available from different repositories, it is up
to the package manager to decide which one to install (usually the
latest, unless you specify a particular version).

(However, if you set `use_local_repo_only: yes`, TPA will disable
all other package repositories, so that instances can only use the
packages that you provide in `local-repo`.)
