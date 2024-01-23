# Barman

When an instance has the `barman` role in `config.yml`, TPA
configures the instance as a [Barman](https://pgbarman.org/) server to take backups
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
their `backup`. Any `postgres` instance can have a list of
Barman servers named as its `backup`. In this case, backups are taken to all
of the named servers.

The default Barman configuration connects to PostgreSQL using
`pg_receivewal` to take continuous backups of WAL. It takes a full
backup of the instance using rsync over ssh twice weekly. Full backups
and WAL are retained for long enough to enable recovery to any point in
the previous 4 weeks.


## Barman configuration

On each Barman server, a global configuration file is created
as `/etc/barman.conf`. This file contains default values for many Barman
configuration variables. For each Postgres server being backed up,
an additional Barman configuration file is created. For example, to back up the
server `one`, the file is `/etc/barman.d/one.conf`, and the backups
are stored in `/var/lib/barman/one`. The file and directory names
are taken from the backed-up instance's `backup_name` setting. The default for this setting
is the instance name.

You can set the following variables on the backed-up instance. They are
passed through into Barman's configuration with the prefix `barman_`
removed.

| Variable | Default |
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

TPA installs a cron job in `/etc/cron.d/barman` that runs every
minute and invokes `barman cron` to perform maintenance tasks.

For each instance being backed up, TPA installs another cron job in
`/etc/cron.d/<backup_name>` that takes the backups of that instance.
This job runs as determined by the `barman_backup_interval` variable for
the instance. The default is to take backups at 04:00 every
Wednesday and Saturday.

## SSH keys

TPA generates ssh key pairs for the postgres and barman
users and installs them into the respective `~/.ssh` directories. Keys for
the postgres user are added to the barman `authorized_keys` file, and
keys for the barman user are added to the postgres `authorized_keys` file.
The postgres user must be
able to ssh to the Barman server to archive WAL segments (if
configured), and the barman user must be able to ssh to the Postgres
instance to take or restore backups.
