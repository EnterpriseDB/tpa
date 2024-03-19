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
- [Adding the *vector* extension through configuration](reconciling-local-changes.md)
- [Specifying extensions for configured databases](postgres_databases.md)
- [Including shared preload entries for extensions](postgresql.conf.md#shared-preload-libraries)
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
- autocluster
- refdata
