# pglogical configuration

TPA can configure pglogical replication sets (publications) and
subscriptions with pglogical v2 and pglogical v3.

```yaml
instances:
- node: 1
  Name: kazoo
  …
  vars:
    publications:
    - type: pglogical
      database: example
      name: some_publication_name
      replication_sets:
      - name: custom_replication_set
        …

- node: 2
  Name: keeper
  vars:
    subscriptions:
    - type: pglogical
      database: example
      name: some_subscription_name
      publication:
        name: some_publication_name
      replication_sets:
        - default
        - default_insert_only
        - custom_replication_set
      …
```

If you define publications or subscriptions with `type: pglogical`, 
the pglogical extension are created by default. But it's up to
you to determine the version to install. For example, subscribe to the
`products/pglogical3/release` repository for pglogical3.

## Introduction

TPA can configure everything needed to replicate changes between
instances using pglogical. It can also alter the replication setup
based on `config.yml` changes.

To publish changes, you define an entry with `type: pglogical` in
`publications`. To subscribe to these changes, you define an entry
with `type: pglogical` in `subscriptions`, as shown in the preceding example.

Pglogical doesn't have a named publication entity (in the sense that
built-in logical replication has `CREATE PUBLICATION`). A publication
in `config.yml` just assigns a name to a collection of replication sets,
and subscriptions can use this name to refer to the desired provider.

To use pglogical replication, both publishers and subscribers need a
named local pglogical node. TPA creates this node with
`pglogical.create_node()` if it doesn't exist. For publications, the
publication name is used as the pglogical node name. There can be only
one pglogical node in any given database, so you can have only one entry
in `publications` per database.

However, pglogical subscriptions *do* have a name of their own. TPA
creates subscriptions with the given `name`. It uses a default
value for the pglogical node name based on the instance's name and the
name of the database in which the subscription is created. You can
specify a different `node_name` if required, for example, when you have
configured a publication in the same database, so that all subscriptions
in that database must share the same pglogical node.

TPA does some basic validation of the configuration. For example, it reports
the error if you misspell `replication_sets` as `replciation_sets` or
try to subscribe to a publication that isn't defined. But it's your
responsibility to specify a meaningful set of publications and
subscriptions.

TPA configures pglogical after creating users, extensions, and
databases but before any PGD configuration. You can set
[`postgres_users`](postgres_users.md) and
[`postgres_databases`](postgres_databases.md) to create databases
for replication and use the
[`postgres-config-final`](tpaexec-hooks.md#postgres-config-final)
hook to populate the databases before pglogical is configured.

## Publications

An entry in `publications` must specify a `name` and `database`,
and can specify a list of named `replication_sets` with optional
attributes, as well as a list of table or sequence names:

```yaml
publications:
- type: pglogical
  database: example
  name: some_publication_name
  replication_sets:
  - name: default
    replicate_insert: true
    replicate_update: true
    replicate_delete: true
    replicate_truncate: true
    autoadd_tables: false
    autoadd_sequences: false
    autoadd_existing: true
  - name: custom_replication_set
    tables:
    - name: sometable
    - name: '"some-schema".othertable'
      columns: [a, b, c]
      row_filter: 'a > 42'
      synchronize_data: true
    sequences:
    - name: someseq
      synchronize_data: true
    - name: '"some-schema".otherseq'
```

Each replication set can specify optional attributes, such as
`replicate_insert` and `autoadd_existing`. If specified, they're
included as named parameters in the call to
`pglogical.create_replication_set()`. Otherwise, they're left out,
and the replication set is created with pglogical's defaults instead.

Apart from manipulating the list of relations belonging to the
replication set using the `autoadd_*` parameters in pglogical3, you
can also explicitly specify a list of tables or sequences. The name of
each relation can be schema-qualified (unqualified names are assumed to
be in `public`). The entry can include optional attributes such as
`row_filter` (for tables only) or `synchronize_data`, as shown
in the preceding example.

## Subscriptions

An entry in `subscriptions` must specify a `name` and `database`,
define a publication to subscribe to, and can specify other optional
attributes of the subscription:

```yaml
subscriptions:
- type: pglogical
  database: example
  name: some_subscription_name
  node_name: optional_pglogical_node_name
  publication:
    name: some_publication_name
  # Optional attributes:
  synchronize_structure: true
  synchronize_data: true
  forward_origins: ['all']
  strip_origins: false
  apply_delay: '1 second'
  writer: 'heap'
  writer_options:
    - 'magic'
    - 'key=value'
    - 'just-a-string'
  # Optional attributes that can be changed for an existing
  # subscription:
  replication_sets:
    - default
    - default_insert_only
    - custom_replication_set
  enabled: true
```

A subscription can set `publication.name` (as shown in the preceding example) to define
the publication to subscribe to. If there's more than one publication
with that name (across the entire cluster), you can specify the name of
an instance to disambiguate. If you want to refer to publications by
name, don't create multiple publications with the same name on the same
instance.

```yaml
- type: pglogical
  …
  publication:
    name: some_publication_name
    instance: kazoo

  # OR

  provider_dsn: "host=… dbname=…"
```

Instead of referring to publications by name, you can explicitly specify
a `provider_dsn`. In this case, the given DSN is passed to
`pglogical.create_subscription()` directly, and `publication` is
ignored. You can use this mechanism to subscribe to instances outside
the TPA cluster.

The other attributes in the example are optional. If defined, they're
included as named parameters in the call to
`pglogical.create_subscription()`. Otherwise, they're left out.
(Some attributes shown are specific to pglogical3.)

## Configuration changes

For publications, you can add or remove replication sets, change the
attributes of a replication set, or change its membership, that is, the tables
and sequences it contains.

If you change `replicate_*` or `autoadd_*`, TPA calls
`pglogical.alter_replication_set()` accordingly. However, you
can't change `autoadd_existing` for existing replication sets, and
the `autoadd_*` parameters are all pglogical3-specific.

If you change the list of `tables` or `sequences` for a replication
set, TPA reconciles these changes by calling
`pglogical.alter_replication_set_{add,remove}_{table,sequence}()` as
needed.

However, if you change `synchronize_data` or other attributes for a
relation (table or sequence) that's already a member of a replication
set, TPA doesn't propagate the changes (for example, by dropping the table
and adding it again with a different configuration).

For subscriptions, you can change only the list of `replication_sets`
and enable or disable the subscription (`enabled: false`).

In both cases, any replication sets that exist but aren't mentioned in
the configuration are removed. (They're removed with
`pglogical.alter_subscription_remove_replication_set()` on the
subscriber or `pglogical.drop_replication_set()` on the
publisher. However, the default replication sets named `default`,
`default_insert_only`, and `ddl_sql` aren't dropped.)

If you edit `config.yml`, remember to run `tpaexec provision` before
running `tpaexec deploy`.

## Interaction with PGD

If you're cautious, it's possible to use PGD and pglogical together in the same database.

PGD v3 uses pglogical3 internally and creates a pglogical node if
one doesn't exist. There can be only one pglogical node per database,
so if you configure a pglogical publication in `bdr_database`, the
instance's `bdr_node_name` must be the same as the publication's `name`.
Otherwise, the node is created for the publication first, and
`bdr.create_node()` will fail later with an error about a node name
conflict. Any `subscriptions` in `bdr_database` must use the same
`node_name` too.

## Limitations

* There's currently no support for
  `pglogical.replication_set_{add,remove}_ddl()`.

* There's currently no support for
  `pglogical.replication_set_add_all_{tables,sequences}()`.

* There's currently no support for
  `pglogical.alter_subscription_{interface,writer_options}()` or
  `pglogical.alter_subscription_{add,remove}_log()`.

* pglogical v1 support isn't currently tested.
