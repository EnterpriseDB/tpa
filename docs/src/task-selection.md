---
description: Selecting which tasks TPA should run during deployment.
---

# Selective task execution

## Using task selectors

You can tell TPA to run only a subset of the tasks that constitute a
full deployment using the `--excluded_tasks`, `--included_tasks`, and
`--opt_in_tasks` options to `tpaexec deploy`. Each of these arguments
is a string treated as a comma-separated list of selectors. Equivalently,
you can set the `excluded_tasks`, `included_tasks`, and `opt_in_tasks`
variables in `config.yml`, either for the whole cluster or for the
separate instances. In `config.yml`, you can use either a
comma-separated string or a yaml list.

### excluded_tasks

Names tasks that should not run. Any task listed here is
unconditionally skipped, even if it would otherwise be enabled by
the other lists. Empty by default; TPA runs every task that
applies to the cluster.

### included_tasks

When non-empty, restricts the deploy to only the named tasks: any
task not in `included_tasks` is implicitly excluded. Useful when you
want to re-run only a specific subset — for example,
`included_tasks: [repmgr]` to re-run only the repmgr setup tasks.
When empty (the default), every task that applies runs.

### opt_in_tasks

Names tasks that should run only when explicitly opted in to. Some
selectors (listed below as "run only when opted in to") are
off-by-default and require an entry here to run. Unlike
`included_tasks`, adding a name to `opt_in_tasks` does *not* engage
whitelist semantics — it enables that one task without saying
anything about any other task.

### Interactions

`excluded_tasks` always wins: a task named there does not run, no
matter what the other lists say. For example, on an AWS cluster
`sysctl_net` is opted in to by default; to disable it again use
`excluded_tasks: [sysctl_net]`.

`included_tasks` and `opt_in_tasks` are independent. A non-empty
`included_tasks` only constrains the set of tasks that would
normally run; it does not by itself enable opt-in tasks. Conversely,
listing a task in `opt_in_tasks` enables that one task whether or
not `included_tasks` is set.

Some selectors may be used in either of the include/exclude lists,
some only in the `excluded_tasks` list, and some only when opted in
to, as detailed below. A separate set of selectors is available for
`tpaexec test`.

## Examples

To deploy without running barman-related tasks:

```shell
tpaexec deploy <clustername> --excluded_tasks=barman
```

To deploy running only repmgr-related tasks:

```shell
tpaexec deploy <clustername> --included_tasks=repmgr
```

To deploy without trying to set hostnames on the instances:

```shell
tpaexec deploy <clustername> --excluded_tasks=hostname
```

To prevent bootstrap and ssh tasks from ever running, put the following
into `config.yml`:

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

    Tasks related to setting up BDR, including when it is as used within
    a PGD cluster. If this selector is excluded, TPA will still install
    and configure the extension as specified in config.yml, but won't
    create the node groups or try to join the nodes.

- create_pgd_proxy_system_user

    Tasks which creates the system user for pgd_proxy

- create_postgres_system_user

    Tasks which creates the system user for postgres

- efm

    Tasks related to EFM.

- etcd

    Tasks related to etcd.

- first-backup

    Tasks which ensure the minimum number of barman backups exist.

- haproxy

    Tasks related to haproxy.

- harp

    Tasks related to harp.

- patroni

    Tasks related to patroni.

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

    Tasks which install packages using the system package manager.

- post-deploy

    The post-deploy hook, if one is defined.

- postgres

    Tasks related to postgres.

- replica

    Tasks which are run and instances acting as postgres replicas.

- repmgr

    Tasks related to repmgr.

- restart

    Tasks which restart services

- sys

    Tasks related to system setup before any tasks specific to postgres
    or related software.

- zabbix-agent

    Tasks related to the zabbix agent.

The following selectors are supported only for exclusion:

- artifacts

    Tasks related to [artifacts](artifacts.md).

- barman-clean

    Tasks which clean up the Barman build directory if Barman is being
    built from source.

- barman-pre-config

    The barman-pre-config hook, if one is defined.

- bdr-pre-node-creation

    The bdr-pre-node-creation hook, if one is defined.

- bdr-post-group-creation

    The bdr-post-group-creation hook, if one is defined.

- bdr-pre-group-join

    The bdr-pre-group-join hook, if one is defined.

- bootstrap

    Tasks which ensure that python and other minimal dependencies are
    present before the rest of the deploy runs. Exclude this only if you
    are sure you have manually installed the relevant requirements.

- build-clean

    Tasks which clean up build directories for any software that is
    being built from source.

- build-configure

    Tasks which configure any software that is being built from source.

- cloudinit

    Tasks which are run only on hosts managed by cloud-init.

- commit-scopes

    Tasks related to configuration of BDR commit scopes.

- config

    Tasks which create config files.

- efm-pre-config

    The efm-pre-config hook, if one is defined.

- efm-post-config

    The efm-post-config hook, if one is defined.

- fs

    Tasks related to setting up additional [volumes](volumes.md) on
    instances.

- hostkeys

    Tasks which set up [ssh host keys](manage_ssh_hostkeys.md).

- hostname

    Tasks which set the hostname.

- hosts

    Tasks which [add entries to /etc/hosts](hosts.md)

- initdb

    Tasks which run initdb.

- local-repo

    Tasks which set up [local package repositories](local-repo.md).

- locale

    Tasks which install [locale support](locale.md).

- openvpn

    Tasks which set up OpenVPN.

- pg-backup-api-clean

    Tasks which clean up the build directory if the Postgres backup API
    is being built from source.

- pgbouncer-config

    Tasks which create configuration files for pgbouncer.

- pgpass

    Tasks which create the [.pgpass](pgpass.md) file.

- post-repo

    The post-repo hook, if one is defined.

- postgres-clean

    Tasks which clean up the build directory if postgres is being built
    from source.

- postgres-config

    The postgres-config hook, if one is defined.

- postgres-config-final

    The postgres-config-final hook, if one is defined.

- pre-deploy

    The pre-deploy hook, if one is defined.

- pre-initdb

    The pre-initdb hook, if one is defined.

- replication-sets

    Tasks related to witness-only replication sets on a BDR3 cluster.

- repmgr-clean

    Tasks which clean up the build directory if repmgr is being built
    from source.

- repmgr-configure

    Tasks which configure repmgr if it is being built from source.

- repo

    Tasks which set up package repositories.

- rsyslog

    Tasks related to rsyslog.

- service

    Tasks related to system services, including configuration and
    restarting.

- src

    Tasks which build and install packages from source.

- ssh

    Tasks related to setting up ssh between instances.

- ssh-cluster-key-config

    Tasks which add the cluster SSH public key to the `ansible_user`'s
    (default: root) authorized_keys file. This can be excluded on
    platforms where authorized_keys is managed externally or is
    read-only.

- sysctl

    Tasks which set and reload sysctl settings.

- sysstat

    Tasks releated to the sysstat service.

- tpa

    Tasks related to TPA's own files installed on instances.

- user

    Tasks related to setting up system users.

- watchdog

    Tasks related to the kernel watchdog on a patroni cluster.

The following selectors run only when opted in to via `opt_in_tasks`:

- sysctl_net

    The TPA-managed network and connection-tuning sysctls
    (`net.core.rmem_max`, `net.core.wmem_max`,
    `net.ipv4.tcp_max_syn_backlog`, `net.ipv4.ip_local_port_range`).
    `tpaexec configure --platform aws` opts the cluster in to this
    selector by default; on other platforms it is opt-in. See
    [Setting sysctl values](sysctl_values.md).

## Supported selectors for `tpaexec test`

The following selectors apply only for execution of `tpaexec test`:

- camo

    Tasks related to testing CAMO in a BDR or PGD cluster.

- ddl

    Tasks related to testing DDL in a BDR or PGD cluster.

- fail

    Tasks which abort tests if a problem is detected. Exclude this
    selector to run tests regardless of failures.

- pgbench

    Tasks which run pgbench.

- sys

    Tasks which run system-level tests.

- barman, bdr, haproxy, pg-backup-api, pgbouncer, pgd-proxy, postgres,
  repmgr,

    Tasks which test the various software components.
