# tpaexec download-packages

The purpose of the downloader is to provide the packages required to do
a full installation of a TPA cluster from an existing configuration.
This capability is useful when you want to ship packages to secure clusters that don't
have internet access or avoid downloading packages repeatedly for
test clusters.

The downloader downloads the full dependency tree of packages
required. The resulting package repository includes metadata
files for the target distribution package manager, so it can be used
exclusively to build clusters. At this time, package managers Apt and YUM
are supported.

!!! Note
    The `download-packages` feature requires Docker installed
    on the TPA host. The downloader operates by creating a
    container of the target operating system and uses that system's package
    manager to resolve dependencies and download all necessary packages. The
    required Docker setup for `download-packages` is the same as when
    [using Docker as a deployment platform](#platform-docker).

## Usage

To use `download-packages`, you need an existing cluster configuration. 
You can create the configuration
using the `tpaexec configure` command. No specific options are required
to create a configuration to use with the downloader. See 
[Configuring a cluster](configure-cluster.md).

Execute the `download-packages` subcommand to start the download process.
Provide the OS and OS version for the downloader to use.

```shell
tpaexec download-packages cluster-dir --os RedHat --os-version 8
```

You can also express this command as a specific Docker image. We strongly
recommend that you use one of the images in `tpa`, as in this example:


```shell
tpaexec download-packages cluster-dir --docker-image tpa/redhat:8
```

By default, the downloader places downloaded files in the directory `local-repo`.
You can download to an alternative directory by using
the option `--download-dir path`.

## Using the result

The contents of the `local-repo` directory is populated with a structure
determined by Ansible according to the OS contained in the Docker image.
This example shows the contents of the Docker image `tpa/redhat:8`:

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
node. See [Recommendations for installing to an air-gapped environment](
air-gapped.md). TPA detects and uses a [local-repo](local-repo.md) automatically.

## Cleaning up failed downloader container

If an error occurs during the download process, the command leaves
behind the downloader container running to help with debugging. For
example, you might want to log in to the failed downloader container to
inspect logs or networking. The downloader container is typically named
`$cluster_name-downloader` unless it exceeds the allowed limit of 64
characters for the container name. You can check for the exact name by
running `docker ps` to list the running containers and look for a container
name that matches your cluster name. In most cases, you can log in to the
running container by executing `docker exec -it $cluster_name-downloader /bin/bash`.
After the inspection, you can clean up the leftover container by running the
`download-packages` command with `--tags cleanup`. For example:

```shell
tpaexec download-packages cluster-dir --docker-image tpa/redhat:8 --tags cleanup
```
