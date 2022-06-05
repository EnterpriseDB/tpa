# tpaexec download-packages

The `tpaexec download-packages` command downloads all of the packages
required by a cluster into a [local repository](local-repo.md), which
will be published to instances in the cluster.

This is useful when you want to ship packages to secure clusters that do
not have internet access, or avoid downloading packages repeatedly for
test clusters.

## Quickstart

```bash
$ tpaexec download-packages ~/clusters/speedy
```

This will create a temporary Docker container within the cluster (which
will not affect existing instances in any way), and

1. Configure all required package repositories on the container

2. Download all required packages and their dependencies into a
   distribution-specific local-repo directory, e.g.,
   `~/clusters/speedy/local-repo/Debian/10` (creating any directories
   that do not exist along the way)

3. Remove the temporary docker container.










