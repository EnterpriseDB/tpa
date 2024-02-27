# Installing packages

TPA installs a batch of non-Postgres-related packages early during
the deployment, then all Postgres-related packages together, and then
packages for optional components separately. These instructions are for
installing packages like sysstat or strace, which have no dependency on
Postgres packages.

You can add entries to `packages` under `cluster_vars` or a
particular instance's `vars` in `config.yml`:

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
    SLES:
      - slespkg1
```

In this example, TPA installs its own list of
`default_packages`, the packages listed under `packages.common`
on every instance, and the remaining distribution-specific packages
based on the distribution the instance is running. If any of these
packages isn't available, the deployment fails.

Don't list any packages that depend on Postgres. Use
[`extra_postgres_packages`](postgres_installation_method_pkg.md)
instead.

## Optional packages

You can specify a list of `optional_packages` that can be installed. They will be
installed if they're available and ignored otherwise. As with the
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

You can specify a list of `unwanted_packages` to
remove if they're installed.

```yaml
unwanted_packages:
  common:
    - badpkg1
  Ubuntu:
    - badpkg2
```
