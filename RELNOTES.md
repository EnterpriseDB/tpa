# TPA release notes

## v2017.11 (not yet tagged)

Features:

- Place provision/deprovision/rehydrate in bin/, and make them location
  independent (i.e., not require to be run from TPA_DIR).

Bugfixes:

- Fix a bug with repmgr/final dying on non-Postgres instances
- Fix some bugs with volume_for/mountpoint declarations

## v2017.10 (2017-10-05)

Features:

- We override the role/upstream settings in config.yml with information
  discovered by querying the cluster, thereby adapting gracefully to
  changes after failover/switchover.

- We no longer try to use Distribution-specific locations and setup
  tools (e.g., pg_createcluster), but instead use initdb to initialise
  PGDATA and install our own service files for Postgres.

- Allow volumes to be retained and reattached to new instances to
  support re-deployments on a new instance with old data volumes.

- Feature parity for postgres/pkg and postgres/src installations.

- Allow replicas to easily specify configuration overrides.

Bugfixes:

- (too many to mention)
