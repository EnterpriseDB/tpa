# Installing packages

TPAexec installs a batch of non-Postgres-related packages early during
the deployment, then all Postgres-related packages together, and then
packages for optional components separately. This page is about
installing packages like sysstat or strace, which have no dependency on
Postgres packages.

You can add entries to `packages` under `cluster_vars` or a
particular instance's `vars` in config.yml:

```yaml
cluster_vars:
  packages:
    common:
      - pkg1
      - pkg2
    Debian:
      - debpkg1
    RedHat:
      - rhpkg1
      - rhpkg2
    Ubuntu:
      - ubpkg1
```

In the example above, TPAexec will install its own list of
`default_packages` and the packages listed under `packages.common`
on every instance, and the remaining distribution-specific packages
based on which distribution the instance is running. If any of these
packages is not available, the deployment will fail.

Don't list any packages that depend on Postgres; use
[`extra_postgres_packages`](postgres_installation_method_pkg.md)
instead.

## Optional packages

You can specify a list of `optional_packages` to install. They will be
installed if they are available, and ignored otherwise. As with the
other settings, the `common` entries apply to every instance, whereas
any other lists apply only to instances running the relevant
distribution.

```yaml
optional_packages:
  common:
    - pkg1
    - pkg2
  Debian:
    - debpkg4
```

## Removing packages

You can specify a list of `unwanted_packages` that should be
removed if they are installed.

```yaml
unwanted_packages:
  common:
    - badpkg1
  Ubuntu:
    - badpkg2
```
