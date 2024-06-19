---
description: Creating Postgres databases during deployment.
---

# Creating Postgres databases

To create Postgres databases during deployment, add entries to the list
of `postgres_databases` under `cluster_vars` or a particular
instance's `vars` in config.yml:

```yaml
cluster_vars:
  postgres_databases:
  - name: exampledb

  - name: complexdb
    owner: example
    encoding: UTF8
    lc_collate: de_DE.UTF-8
    lc_ctype: de_DE.UTF-8
    template: template0
    extensions:
    - name: hstore
    - name: dblink
    languages:
    - name: plperl
    - name: plpython
    tablespace: exampletablespace
```

The example above would create two databases (apart from any databases
that TPA itself decides to create, such as `bdr_database`).

Each entry must specify the `name` of the database to create. All
other attributes are optional.

The `owner` is `postgres` by default, but you can set it to any
valid username (the users in [`postgres_users`](postgres_users.md)
will have been created by this time).

The `encoding`, `lc_collate`, and `lc_ctype` values default to the
`postgres_locale` set at the time of running initdb (the default is to
use the target system's LC_ALL or LANG setting). If you are creating a
database with non-default locale settings, you will also need to specify
`template: template0`.

You can optionally specify the default `tablespace` for a database; the
tablespace must already exist
(see [`postgres_tablespaces`](postgres_tablespaces.md)).

You can specify optional lists of `extensions` and `languages` to create
within each database (in addition to any extensions or languages
inherited from the template database). Any packages required must be
installed already, for example by including them in
[`extra_postgres_packages`](postgres_installation_method_pkg.md).

TPA will not drop existing databases that are not mentioned in
`postgres_databases`, and it may create additional databases if required
(e.g., for BDR).
