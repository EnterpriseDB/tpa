---
description: Configuring Barman for backup and recovery with TPA.
---

# Barman

When an instance is given the `barman` role in config.yml, TPA will
configure it as a [Barman](https://pgbarman.org/) server to take backups
of any other instances that name it in their `backup` setting.

```yaml
instances:
- Name: one
  backup: two
  …

- Name: two
  role:
  - barman
  …
```

Multiple `postgres` instances can have the same Barman server named as
their `backup`; equally, one `postgres` instance can have a list of
Barman servers named as its `backup` and backups will be taken to all
of the named servers.

The default Barman configuration will connect to PostgreSQL using
pg_receivewal to take continuous backups of WAL, and will take a full
backup of the instance using rsync over ssh twice weekly. Full backups
and WAL are retained for long enough to enable recovery to any point in
the last 4 weeks.


## Barman configuration

The Barman home directory on the Barman server can be set using the
cluster variable `barman_home`; its default value is `/var/lib/barman`.

On each Barman server, a global configuration file is created
as `/etc/barman.conf`. This file contains default values for many Barman
configuration variables. For each Postgres server being backed up,
an additional Barman configuration file is created. For example, to back up the
server `one`, the file is `/etc/barman.d/one.conf`, and the backups
are stored in the subdirectory `one` in the Barman home directory. The
configuration file and directory names are taken from the backed-up instance's
`backup_name` setting. The default for this setting is the instance name.

The following variables can be set on the backed-up instance and are
passed through into Barman's configuration with the prefix `barman_`
removed:

| variable | default |
|----------|---------|
| barman_archiver | false |
| barman_log_file | /var/log/barman.log |
| barman_backup_method |  rsync |
| barman_compression | pigz |
| barman_reuse_backup | link |
| barman_parallel_jobs | 1 |
| barman_backup_options | concurrent_backup |
| barman_immediate_checkpoint | false |
| barman_network_compression | false |
| barman_basebackup_retry_times | 3 |
| barman_basebackup_retry_sleep | 30 |
| barman_minimum_redundancy | 3 |
| barman_retention_policy | RECOVERY WINDOW OF 4 WEEKS |
| barman_last_backup_maximum_age | 1 WEEK |
| barman_pre_archive_retry_script | |
| barman_post_backup_retry_script | |
| barman_post_backup_script | |
| barman_streaming_wals_directory | |


## Backup scheduling

TPA installs a cron job in `/etc/cron.d/barman` which will run every
minute and invoke `barman cron` to perform maintenance tasks.

For each instance being backed up, it installs another cron job in
`/etc/cron.d/<backup_name>` which takes the backups of that instance.
This job runs as determined by the `barman_backup_interval` variable for
the instance, with the default being to take backups at 04:00 every
Wednesday and Saturday.

## SSH keys

TPA will generate ssh key pairs for the `postgres` and `barman`
users and install them into the respective ~/.ssh directories, and add
them to each other's authorized_keys file. The postgres user must be
able to ssh to the barman server in order to archive WAL segments (if
configured), and the barman user must be able to ssh to the Postgres
instance to take or restore backups.

## `barman` and `barman_role` Postgres users

TPA will create two Postgres users, `barman` and `barman_role`.

TPA versions `<23.35` created the `barman` Postgres user as a `superuser`.

Beginning with `23.35` the `barman` user is created with `NOSUPERUSER`,
so any re-deploys on existing clusters will remove the `superuser` attribute
from the `barman` Postgres user. Instead, the `barman_role` is granted the 
required set of privileges and the `barman` user is granted `barman_role` membership. 

This avoids granting the `superuser` attribute to the `barman` user, using the set
of privileges provided in the [Barman Manual](https://docs.pgbarman.org/release/latest/#postgresql-connection).

