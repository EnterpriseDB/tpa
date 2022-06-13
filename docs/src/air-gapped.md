# Managing clusters in a disconnected or Air-Gapped environment

In a security controlled environment where no direct connection to the
Internet is allowed, it is necessary to provide all packages needed by
TPAexec to manage clusters. This can be done via a dedicated package
repository or via a local-repo on each node in the cluster. TPAexec
supports the addition of custom repositories on each node via a
[local-repo](local-repo.md) and the required packages can be downloaded
using the [download-packages](tpaexec-download-packages.md) command.

## Preparation

On an internet connected machine where you can install TPAexec, create a
new cluster or copy an existing cluster config.yml into a directory.

Note: that you do not need separate cluster configurations for internet
connected and disconnected environments, the options below work in both.

For an environment where the target instances will not have network
access, configure a new cluster with this option:

    tpaexec configure --use-local-repo-only …

This will do everything that `--enable-local-repo` does, and disable the
configuration for all other package repositories. On RedHat instances,
this also includes disabling access to subscription-based services.

In an existing cluster, you can set `use_local_repo_only: yes` in
`config.yml`:

```yaml
cluster_vars:
    use_local_repo_only: yes
```

More info on [using local-repo for distributing packages](local-repo.md)

## Downloading packages

On the internet connected machine, ensure that you
have [docker installed](INSTALL-docker.md) and run:

```shell
tpaexec download-packages cluster-dir --os <OS> --os-version <version>
```

See detailed description for
the [package downloader](tpaexec-download-packages.md).

## Promoting artifacts to target environment

The resulting repository will be contained in the
`cluster-dir/local-repo` directory. This is a complete package repo for
the target OS. Copy this directory to the target environment to the
control node that will be used to deploy the cluster. Place the
directory in the same place, beneath the cluster directory.

## Deploying in a disconnected environment

Ensure that the cluster config.yml has been configured as above in
[Preparation](#preparation). Run `tpaexec provision` and `deploy` as you
would normally.
