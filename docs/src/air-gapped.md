# Managing clusters in a disconnected or air-gapped environment

In a security-controlled environment where no direct connection to the
Internet is allowed, you need to provide all packages needed by
TPA to complete the deployment. You can do this by way of `local-repo` on
each node in the cluster. TPA supports the addition of custom
repositories on each node by way of
[`local-repo`](local-repo.md). You can can download the required packages
using the [`download-packages`](tpaexec-download-packages.md) command.

## Preparation

Choose an internet-connected machine where you can install TPA. 
Follow these instructions to either copy an existing cluster
configuration or create a new cluster.

!!! Note
    If TPA isn't already installed on the air-gapped server,
    follow [these instructions](INSTALL.md#installing-tpa-without-internet-or-network-access-air-gapped)
    to install it.

If you have an existing cluster in a disconnected environment, all you
need on the internet-connected host is the `config.yml` file. Create a
directory and copy that file into it. Then run `tpaexec relink` on that
directory to generate the remaining files that are normally created
by `tpaexec configure`.

Alternatively, to create a new configuration for an environment where
the target instances doesn't have network access, configure a new
cluster using this option:

```
    tpaexec configure --use-local-repo-only …
```

This command does everything that `--enable-local-repo` does and disables the
configuration for all other package repositories. On RedHat instances,
it also disables access to subscription-based services.

In an existing cluster, you can set `use_local_repo_only: yes` in
`config.yml`:

```yaml
cluster_vars:
    use_local_repo_only: yes
```

You don't need separate cluster configurations for internet-connected 
and disconnected environments. The options that follow work in both.

See [Creating and using a local repository](local-repo.md) for more information.

## Downloading packages

On the internet-connected machine with
[docker installed](platform-docker.md), run:

```shell
tpaexec download-packages cluster-dir --os <OS> --os-version <version>
```

See the detailed description for
the [package downloader](tpaexec-download-packages.md).

## Copying packages to the target environment

The resulting repository is in the
`cluster-dir/local-repo` directory. This is a complete package repo for
the target OS. Copy this directory from the connected controller to the
disconnected controller that will be used to deploy the cluster. Place
the directory in the same place, beneath the cluster directory. TPA
then copies packages to the instances when you run `deploy`.

## Deploying in a disconnected environment

Make sure that the cluster `config.yml` is configured as described in
[Preparation](#preparation). Run `tpaexec provision` and `deploy` as you
do normally.

## Updating in a disconnected environment

You can use the [`upgrade`](tpaexec-upgrade.md) command to
perform updates in an air-gapped environment. Before running this
command, you must run `download-packages` on the connected controller and
copy the updated repository to the disconnected controller.
