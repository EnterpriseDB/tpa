# Installing Postgres-related packages

TPA installs a batch of non-Postgres-related packages early during
the deployment, then all Postgres-related packages together, and then
packages for optional components separately. These instructions are for
installing packages like pglogical that depend on Postgres.

To install extra packages that depend on Postgres (for example, Postgis), list
them under `extra_postgres_packages` in `cluster_vars` or a
particular instance's `vars` in `config.yml`:

```yaml
cluster_vars:
  extra_postgres_packages:
    common:
      - postgres-pkg1
      - postgres-pkg2
    Debian:
      - postgres-deb-pkg1
    RedHat:
      - postgres11-rhpkg1
      - postgres11-rhpkg2
    Ubuntu:
      - ubpkg1
    SLES:
      - slespkg1
```

The packages listed under `packages.common` will be installed on every
instance, together with the default list of Postgres packages and any
distribution-specific packages you specify.

See also
[compiling and installing Postgres from source](postgres_installation_method_src.md).
