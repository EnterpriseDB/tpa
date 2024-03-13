# Adding Postgres extensions

## Default Postgres extensions
By default, TPA adds the following extensions to every Postgres database.
If needed, it adds the corresponding entries into shared
preload libraries.

  - pg_stat_statements
  - pg_freespacemap
  - pg_visibility
  - pageinspect
  - pgstattuple

## User-defined extensions
You can specify additional extensions in `config.yml` by
specifying the extension name, any required shared preload entries, and
the package containing the extension. See:
- [Adding the *vector* extension through configuration](reconciling-local-changes.md)
- [Specifying extensions for configured databases](postgres_databases.md)
- [Including shared preload entries for extensions](postgresql.conf.md#shared-preload-libraries)
- [Installing Postgres-related packages](postgres_installation_method_pkg.md)

## TPA-recognized extensions
The following extensions require you to add only the extension name
in `config.yml`. You can add the name either to `extra_postgres_extensions` or to the
`extensions` list of a database specified in `postgres_databases`. TPA 
includes the correct package and any required
entries in `shared_preload_libraries`.
- edb_pg_tuner
- query_advisor
- edb_wait_states
- sql_profiler
- autocluster
- refdata
