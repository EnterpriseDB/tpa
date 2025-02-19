---
description: Enabling the pg-backup-api and configuring client cert authentication.
---

# PG Backup API

If you set `enable_pg_backup_api: true` in `config.yml` or use the
`--enable-pg-backup-api` command line option during configure, instances
with the `barman` role will install pg-backup-api and set up an
apache proxy for client cert authentication. This apache proxy will use
an SSL CA generated for the cluster to generate its server and client
certificates.

```yaml
cluster_vars:
  enable_pg_backup_api: true
```

## PG Backup API package version

By default, TPA installs the latest available version of pg-backup-api.

The version of the pg-backup-api package that is installed can be specified 
by including `pg_backup_api_package_version: xxx` under the `cluster_vars` 
section of the `config.yml` file.

```yaml
cluster_vars:
    …
    pg_backup_api_package_version: '2.0.0-1.el8'
    …
```

You may use any version specifier that apt or yum would accept.

If your version does not match, try appending a `*` wildcard. This
is often necessary when the package version has an epoch qualifier
like `2:...`.


# Installation Options

pg-backup-api will be installed via packages by default, but you can
also install from a git branch or a local directory. See
[configure-source.md](configure-source.md) and
[install_from_source.md](install_from_source.md) for more details.

# Verify Setup

Run `pg-backup-api status` on the barman node running pg-backup-api - if
you get "OK" back, the pg-backup-api service is running.

To test that the proxy is working, run

```shell
curl --cert /etc/tpa/pg-backup-api/pg-backup-user.crt \
     --key /etc/tpa/pg-backup-api/pg-backup-user.key \
     -X GET https://{hostname}/diagnose
```

If it's working, you'll get a large json output. You can compare this
with the output of `barman diagnose`, they should match exactly.

# SSL Certificates

The root certificate will be copied to
`/etc/tpa/pg-backup-api/` by default.

A client certificate and key (`pg-backup-user.crt`and
`pg-backup-user.key`) will be generated for testing (through
`tpaexec test`) or command line from the barman host. See
[Testing](tpaexec-test).

An apache proxy server certificate and key (`pg-backup-api.crt` and
`pg-backup-api.key`) will also be generated

Each service needing to query the api will need to generate its own
client certificate separately. PEM agent role, for instance, generates a
client certificate during it's setup when both `--enable-pem` and
`--enable-pg-backup-api` (or config.yml equivalent) are used.
