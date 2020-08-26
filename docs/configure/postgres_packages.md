# Installing Postgres-related packages

TPAexec installs a batch of non-Postgres-related packages early during
the deployment, then all Postgres-related packages together, and then
packages for optional components separately. This page is about
installing packages like pglogical that depend on Postgres itself.

There's a separate page about
[installing non-Postgres-related packages](packages.md).

To install extra packages that depend on Postgres (e.g., Postgis), list
them under ``extra_postgres_packages`` in ``cluster_vars`` or a
particular instance's ``vars`` in config.yml:

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
```

The packages listed under ``packages.common`` will be installed on every
instance, together with the default list of Postgres packages, and any
distribution-specific packages you specify.
