---
description: Postgres extensions and how to configure them with TPA.
---

# Adding Postgres extensions

## Default Postgres extensions
By default, TPA adds the following extensions to every Postgres database
(and if needed, automatically adds the corresponding entries into shared
preload libraries)

  - pg_stat_statements
  - pg_freespacemap
  - pg_visibility
  - pageinspect
  - pgstattuple

## User defined extensions
Additional extensions can be configured within `config.yml`, by
specifying the extension name, any required shared preload entries and
the package containing the extension. 

When adding extensions, be sure to include both the package name to `extra_postgres_packages` 
and the extension name under `extra_postgres_extensions` (or to the `extensions` list of a
database defined under `postgres_databases`). 

If the extension requires, add the shared preload entry name for the extension to
the `preload_extensions` list. Note this name may differ from the extension name itself, 
so be sure to check the extension's own documentation.

Here is a quick example for an extension that requires to be added to the shared preload extension list
with a different entry for extension and library name.
```yaml
cluster_vars:
  [...]
  extra_postgres_packages:
    - postgresql-17-my-extension
  extra_postgres_extensions:
    - my-extension
  preload_extensions:
    -  my_extension
```

The following sections provide further information.

- [Adding the *vector* extension through configuration](reconciling-local-changes.md)
- [Specifying extensions for configured databases](postgres_databases.md)
- [Including shared preload entries for extensions](postgresql.conf.md#shared_preload_libraries)
- [Installing Postgres-related packages](postgres_installation_method_pkg.md)

## TPA recognized extensions
The following list of extensions only require the extension name to be
added in `config.yml` (either to `extra_postgres_extensions` OR to the
`extensions` list of a database specified in `postgres_databases`) and
TPA will automatically include the correct package and any required
entries to shared_preload_libraries.
- edb_pg_tuner
- query_advisor
- edb_wait_states
- sql_profiler
- pg_failover_slots
- sql_protect
- edb_stat_monitor
- autocluster
- refdata
- bluefin
- postgis
- pgaudit
- passwordcheck
