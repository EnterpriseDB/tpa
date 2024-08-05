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

| variable                        | default                    |
| ------------------------------- | -------------------------- |
| barman_archiver                 | false                      |
| barman_log_file                 | /var/log/barman.log        |
| barman_backup_method            | rsync                      |
| barman_compression              | pigz                       |
| barman_reuse_backup             | link                       |
| barman_parallel_jobs            | 1                          |
| barman_backup_options           | concurrent_backup          |
| barman_immediate_checkpoint     | false                      |
| barman_network_compression      | false                      |
| barman_basebackup_retry_times   | 3                          |
| barman_basebackup_retry_sleep   | 30                         |
| barman_minimum_redundancy       | 3                          |
| barman_retention_policy         | RECOVERY WINDOW OF 4 WEEKS |
| barman_last_backup_maximum_age  | 1 WEEK                     |
| barman_pre_archive_retry_script |                            |
| barman_post_backup_retry_script |                            |
| barman_post_backup_script       |                            |
| barman_streaming_wals_directory |                            |

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

## Shared Barman server

!!! Note

    To use the shared Barman functionality with clusters created using a
    TPA version earlier than 23.35, you must:
    a) upgrade to a version of TPA that supports creating
    shared Barman instances.
    b) after upgrading TPA, run deploy on $first-cluster so TPA can make
    necessary config changes for subsequent clusters to run smoothly
    against the shared Barman node.

Some deployments may want to share a single Barman server for multiple
clusters. Shared Barman server deployment within
tpaexec is supported via the `barman_shared` setting that can be set via
`vars:` under the Barman server instance for the given cluster config
that plans to use an existing Barman server. `barman_shared` is a
boolean variable so possible values are true and false(default). When
making any changes to the Barman config in a shared scenario, you must
ensure that configurations across multiple clusters remain in sync so as
to avoid a scenario where one cluster adds a specific configuration and
a second cluster overrides it.

A typical workflow for using a shared Barman server across multiple
clusters is described below.

1. Create a TPA cluster with an instance that has `barman` role
   (call it 'first-cluster' for this example).
2. In the second cluster (second-cluster for example), reference this
   particular Barman instance from $clusters/first-cluster as a shared
   Barman server instance and use `bare` as platform so we are not
   trying to create a new Barman instance when running provision. Also
   specify the IP address of the Barman instance that this cluster can
   use to access it.

    ```yml
    - Name: myBarman
      node: 5
      role:
          - barman
      platform: bare
      ip_address: x.x.x.x
      vars:
          barman_shared: true
    ```

3. Once the second-cluster is provisioned but before running deploy,
   make sure that it can access the Barman server instance via ssh. You
   can allow this access by copying second-cluster's public key to
   Barman server instance via `ssh-copy-id` and then do an ssh to
   make sure you can login without having to specify the password.

    ```bash
    # add first-cluster's key to the ssh-agent
    $ cd $clusters/first-cluster
    $ ssh-add id_first-clutser
    $ cd $clusters/second-cluster
    $ ssh-keyscan -t rsa,ecdsa -4 $barman-server-ip >> tpa_known_hosts
    $ ssh-copy-id -i id_second-cluster.pub -o 'UserKnownHostsFile=tpa_known_hosts' $user@$barman-server-ip
    $ ssh -F ssh_config $barman-server
    ```

4. Copy the Barman user's keys from first-cluster to second-cluster
    ```bash
    $ mkdir $clusters/second-cluster/keys
    $ cp $clusters/first-cluster/keys/id_barman* clusters/second-cluster/keys
    ```
5. Run `tpaexec deploy $clusters/second-cluster`

!!! Note

    You must use caution when setting up clusters that share a Barman 
    server instance. There are a number of important aspects you must
    consider before attempting such a setup. For example:

    1. Making sure that no two instances in any of the clusters sharing a
    Barman server use the same name.
    2. Barman configuration and settings otherwise should remain in sync in
    all the clusters using a common Barman server to avoid a scenario
    where one cluster sets up a specific configuration and the others do
    not either because the configuration is missing or uses a different
    value.
    3. Version of Postgres on instances being backed up across different
    clusters needs to be the same.
    4. Different clusters using a common Barman server cannot specify
    different versions of Barman packages when attempting to override
    default.

Some of these may be addressed in a future release as we continue to
improve the shared Barman server support.

!!! Warning
Be extremely careful when deprovisioning clusters sharing a common
Barman node. Especially where the first cluster that deployed Barman
uses non-bare platform. Deprovisioning the first cluster that
originally provisioned and deployed Barman will effectively leave
other clusters sharing the Barman node in an inconsistent state
because the Barman node will already have been deprovisioned by the
first cluster and it won't exist anymore.
!!!
