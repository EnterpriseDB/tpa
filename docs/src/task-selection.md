# Selective task execution

## Using task selectors

You can tell TPA to run only a subset of the tasks that constitute a
full deployment using the `--excluded_tasks` and `--included_tasks`
options to `tpaexec deploy`. Each of these arguments is a
string treated as a comma-separated list of selectors. Alternatively, you can set the
`excluded_tasks` and `included_tasks` variables in `config.yml`, either
for the whole cluster or for the separate instances. In `config.yml`,
you can use either a comma-separated string or a yaml list.

Tasks matched by `excluded_tasks` are always excluded. If you specify
`included_tasks`, then non-matching tasks are implicitly excluded.

Some selectors can be used in either list, and some only in the
`excluded_tasks` list, as detailed in
[Supported selectors for `tpaexec deploy`](#supported-selectors-for-tpaexec-deploy). 
A separate set of selectors is available for `tpaexec test`.

## Examples

To deploy without running Barman-related tasks:

```
[tpa]$ tpaexec deploy <clustername> --excluded_tasks barman
```

To deploy running only repmgr-related tasks:

```
[tpa]$ tpaexec deploy <clustername> --included_tasks repmgr
```

To deploy without trying to set hostnames on the instances:

```
[tpa]$ tpaexec deploy <clustername> --excluded_tasks hostname
```

To prevent bootstrap and SSH tasks from ever running, add the following
to `config.yml`:

```yaml
    cluster_vars:
      excluded_tasks:
        - bootstrap
        - ssh
```

## Supported selectors for `tpaexec deploy`

The following selectors are supported for either inclusion or exclusion:

- barman

    Tasks related to Barman.

- bdr

    Tasks related to setting up BDR, including when it's used within
    a PGD cluster. If you exclude this selector, TPA will still install
    and configure the extension as specified in `config.yml`, but it won't
    create the node groups or try to join the nodes.

- efm

    Tasks related to EFM.

- etcd

    Tasks related to etcd.

- first-backup

    Tasks that ensure the minimum number of Barman backups exist.

- haproxy

    Tasks related to Haproxy.

- harp

    Tasks related to Harp.

- patroni

    Tasks related to Patroni.

- pem-agent

    Tasks related to the PEM agent.

- pem-server

    Tasks related to the PEM server.

- pem-webserver

    Tasks related to configuring the web server on a PEM server.

- pg-backup-api

    Tasks related to Barman's Postgres backup API.

- pgbouncer

    Tasks related to PgBouncer.

- pgd-proxy

    Tasks related to PGD Proxy.

- pglogical

    Tasks related to pglogical.

- pkg

    Tasks that install packages using the system package manager.

- postgres

    Tasks related to Postgres.

- replica

    Tasks that run on instances acting as Postgres replicas.

- repmgr

    Tasks related to repmgr.

- restart

    Tasks that restart services.

- sys

    Tasks related to system setup before any tasks specific to Postgres
    or related software.

- zabbix-agent

    Tasks related to the Zabbix agent.

The following selectors are supported only for exclusion:

- artifacts

    Tasks related to [artifacts](artifacts.md).

- barman-clean

    Tasks that clean up the Barman build directory if Barman is being
    built from source.

- bootstrap

    Tasks that ensure that Python and other minimal dependencies are
    present before the rest of the deploy runs. Exclude this only if you're
    sure you manually installed the relevant requirements.

- build-clean

    Tasks that clean up build directories for any software that's
    being built from source.

- build-configure

    Tasks that configure any software that's being built from source.

- cloudinit

    Tasks that are run only on hosts managed by cloud-init.

- commit-scopes

    Tasks related to configuration of BDR commit scopes.

- config

    Tasks that create config files.

- fs

    Tasks related to setting up additional [volumes](volumes.md) on
    instances.

- hostkeys

    Tasks that set up [SSH host keys](manage_ssh_hostkeys.md).

- hostname

    Tasks that set the hostname.

- hosts

    Tasks that [add entries to /etc/hosts](hosts.md).

- initdb

    Tasks that run initdb.

- local-repo

    Tasks that set up [local package repositories](local-repo.md).

- locale

    Tasks that install [locale support](locale.md).

- openvpn

    Tasks that set up OpenVPN.

- pg-backup-api-clean

    Tasks that clean up the build directory if the Postgres backup API
    is being built from source.

- pgbouncer-config

    Tasks that create configuration files for PgBouncer.

- pgpass

    Tasks that create the [.pgpass](pgpass.md) file.

- postgres-clean

    Tasks that clean up the build directory if Postgres is being built
    from source.

- replication-sets

    Tasks related to witness-only replication sets on a BDR3 cluster.

- repmgr-clean

    Tasks that clean up the build directory if repmgr is being built
    from source.

- repmgr-configure

    Tasks that configure repmgr if it's being built from source.

- repo

    Tasks that set up package repositories.

- rsyslog

    Tasks related to rsyslog.

- service

    Tasks related to system services, including configuring and
    restarting.

- src

    Tasks that build and install packages from source.

- ssh

    Tasks related to setting up SSH between instances.

- sysctl

    Tasks that set and reload sysctl settings.

- sysstat

    Tasks related to the sysstat service.

- tpa

    Tasks related to TPA's own files installed on instances.

- user

    Tasks related to setting up system users.

- watchdog

    Tasks related to the kernel watchdog on a Patroni cluster.

## Supported selectors for `tpaexec test`

The following selectors apply only for execution of `tpaexec test`:

- camo

    Tasks related to testing CAMO in a BDR or PGD cluster.

- ddl

    Tasks related to testing DDL in a BDR or PGD cluster.

- fail

    Tasks that abort tests if a problem is detected. Exclude this
    selector to run tests regardless of failures.

- pgbench

    Tasks that run pgbench.

- sys

    Tasks that run system-level tests.

- barman, bdr, haproxy, pg-backup-api, pgbouncer, pgd-proxy, postgres,
  repmgr,

    Tasks that test the various software components.
