---
description: The command that downloads packages for a TPA cluster.
---


# tpaexec download-packages

The purpose of the downloader is to provide the packages required to do
a full installation of a TPA cluster from an existing configuration.
This is useful when you want to ship packages to secure clusters that do
not have internet access, or avoid downloading packages repeatedly for
test clusters.

The downloader will download the full dependency tree of packages
required, and the resulting package repository will include metadata
files for the target distribution package manager, so can be used
exclusively to build clusters. At this time package managers Apt and YUM
are supported.

!!! Note
    The download-packages feature requires Docker to be installed
    on the TPA host. This is because the downloader operates by creating a
    container of the target operating system and uses that system's package
    manager to resolve dependencies and download all necessary packages. The
    required Docker setup for download-packages is the same as that for
    [using Docker as a deployment platform](#platform-docker).

## Usage

An existing cluster configuration needs to exist which can be achieved
using the `tpaexec configure` command. No specific options are required
to use the downloader. See [configuring a cluster](configure-cluster.md)
.

Execute the download-packages subcommand to start the download process.
Provide the OS and OS version that should be used by the downloader.

```shell
tpaexec download-packages cluster-dir --os RedHat --os-version 8
```

This can also be expressed as a specific docker image. It is strongly
recommended that you use one of the tpa images prefixed like the example
below.

```shell
tpaexec download-packages cluster-dir --docker-image tpa/redhat:8
```

The downloader will place files downloaded in the directory `local-repo`
by default. It is possible to download to alternative directory by using
the option `--download-dir path`.

## Using the result

The contents of the `local-repo` directory is populated with a structure
determined by ansible according to the OS contained in the docker image.
For example, the docker image `tpa/redhat:8` would have the following:

```
cluster-dir/
`-- local-repo
    `-- RedHat
        `-- 8
            |-- *.rpm
            `-- repodata
                `-- *repodata-files*
```

You can use this in the cluster as is or copy it to a target control
node. See [recommendations for installing to an air-gapped environment](
air-gapped.md). A [local-repo](local-repo.md) will be detected and used
automatically by TPA.

## Cleaning up failed downloader container

If there is an error during the download process, the command will leave
behind the downloader container running to help with debugging. For
instance you may want to log in to the failed downloader container to
inspect logs or networking. Downloader container is typically named
$cluster_name-downloader unless it exceeds the allowed limit of 64
characters for the container name. You can check for the exact name by
running `docker ps` to list the running containers and look for a container
name that matches your cluster name. In most cases you can log in to the
running container by executing `docker exec -it $cluster_name-downloader /bin/bash`.
After the inspection, you can clean up the left over container by running the
`download-packages` command with `--tags cleanup`. For example:

```shell
tpaexec download-packages cluster-dir --docker-image tpa/redhat:8 --tags cleanup
```
