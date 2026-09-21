---
description: Installing and configuring Postgres Enterprise Manager (PEM) with TPA.
---

# Configuring Postgres Enterprise Manager (PEM)

TPA will install and configure PEM when `tpaexec configure` command is run
with `--enable-pem` command line option.

The default behavior with `--enable-pem` is to enable `pem-agent` role for all
`postgres` instances in the cluster. `pem-agent` role will also be added to
barman nodes when `--enable-pg-backup-api` command line option is used
alongside `--enable-pem`.

Since PEM server uses postgres backend; the PEM server instance implicitly uses
`postgres` role as well which ensures that the PEM server gets a valid postgres
cluster configured for use as PEM backend. All configuration options available
for a normal postgres instance are valid for PEM's backend postgres instance
as well. See following for details:

* [Configure pg_hba.conf](pg_hba.conf.md)
* [Configure postgresql.conf](postgresql.conf.md)

Note that PEM is only available via EDB's package repositories and therefore
requires a valid subscription.

## Supported architectures

PEM is supported with all architectures via the `--enable-pem`
configuration command line option, with the exception of the
BDR-Always-ON architecture when used with EDB Postgres Extended.
You can optionally edit the generated
cluster config (config.yml) and assign or remove `pem-agent` role from any
postgres instance in the cluster in order to enable or disable PEM there.

## PEM component package versions

By default, TPA installs the latest available version of PEM agent and PEM server.

The version of the PEM agent and PEM server packages that are installed can be specified
by including `pem_agent_package_version: xxx`  and `pem_server_package_version: xxx` under
the `cluster_vars` section of the `config.yml` file.

```yaml
cluster_vars:
    …
    pem_agent_package_version: '9.7.0-1.el9'
    pem_server_package_version: '9.7.0-1.el9'
    …
```

You may use any version specifier that apt or yum would accept.

If your version does not match, try appending a `*` wildcard. This
is often necessary when the package version has an epoch qualifier
like `2:...`.

## PEM configuration

TPA will configure pem agents and pem server with the appropriate
instance-specific settings, with remaining settings set to the respective
default values. Some of the configuration options may be exposed for user
configuration at some point in future.

!!! Note PEM components are upgraded independently.
Passing `pem-server` to `--components` upgrades ONLY the PEM server, whereas passing `pem-agent` upgrades ONLY the PEM agents.
If upgrading separately, it is recommended to upgrade the agents before the server. When both are upgraded together, TPA upgrades the agents before the server.
!!!

Obtain the password for the web interface by running
`tpaexec show-password $clusterdir $user`.

## Passing additional options when registering PEM agents

TPA registers each PEM agent in the cluster using the `pemworker` utility's
`--register agent` command.

A list of additional registration options can be
passed by including `pemagent_registration_opts` in the cluster config.

For example:

```yaml
  pemagent_registration_opts:
  - --enable-smtp true
  - --enable-heartbeat-connection
  - --allow-batch-probes true
  - -l DEBUG1
```

The [PEM documentation](https://www.enterprisedb.com/docs/pem/latest/registering_agent/#registering-a-pem-agent-using-the-pemworker-utility)
lists more information about registration options.


## Useful extensions for the nodes with pem agent

By default, TPA will add `sql_profiler`, `edb_wait_states` and
`query_advisor` extensions to any instances that have `pem-agent` role.

This list of default extensions for pem-agent nodes can be overriden by
setting `pemagent_extensions` in config.yml.

If this list is empty, no extensions will be automatically included.

## Providing an external certificate for PEM server SSL authentication

By default, the PEM server creates a self-signed certificate pair,
`server-pem.crt` and `server-pem.key` and configures the webserver to use them
for HTTPS access.

The size of `server-pem.key` can be modified adding the variable `pem_rsa_key_size`
to the `cluster_vars` section:

```yaml
  (...)
  cluster_vars:
    pem_rsa_key_size: 4096
```

The size of the CA certificate expedited by the PEM database can also be modified
adding the variable `pem_db_ca_certificate_key_size` to the `cluster_vars` section:

```yaml
  (...)
  cluster_vars:
    pem_db_ca_certificate_key_size: 4096
```

By default, the self-signed TLS certificate has a period of 10 years.
The period can be adjusted by defining `openssl_certificate_validity` in
the `cluster_vars` section. If the certificate needs to be replaced,
use the `pem_web_server_renew_tls_certificates` variable on `tpaexec deploy`:
`tpaexec deploy (...) -e pem_web_server_renew_tls_certificates=true`.

To provide your own certificate pair, create a directory under the root of the
cluster directory named `ssl/pemserver` and place the certificate pair inside.

```yaml
cluster directory
├── ssl
│   └── pemserver
│       ├── externally-provided.crt
│       └── externally-provided.key
```

Next, set the variables `pem_server_ssl_certificate` and `pem_server_ssl_key`
with the respective file names as values for the `vars:` under the pem server
instance or `cluster_vars` in the cluster config file.

TPA will handle copying these files over to the pem server instance and
configure the webserver accordingly.

```yaml
- Name: my-pem-server
  location: main
  node: 4
  role:
  - pem-server
  vars:
    pem_server_ssl_certificate: externally-provided.crt
    pem_server_ssl_key: externally-provided.key
```

## Organising instances in PEM

PEM supports collating servers and/or agents into **groups** and **clusters**.
You can specify this grouping from TPA by setting the following instance variables.

On instances with the `pem-agent` role, but without `pem-server` role:

- `monitoring_group` specifies the name of the group to which the Postgres server on this instance will be assigned. If not specified it defaults to the value of `pem_server_group`.
- `monitoring_agent_group` specifies the name of the group to which the PEM agent on this instance will be assigned. If not specified it defaults to the value of `pem_agent_group`.
- `monitoring_cluster` specifies the name of the cluster to which the Postgres server on this instance will be assigned. If not specified, no cluster will be assigned/created.
- `monitoring_agent_cluster` specifies the name of the cluster to which the PEM agent on this instance will be assigned. If not specified, no cluster will be assigned/created.

!!!Note
PEM only permits a given cluster name to exist in a single group, so some combinations of these values are not viable.
For example if you specify the same `monitoring_cluster` and `monitoring_agent_cluster`, but different `monitoring_group` and `monitoring_agent_group`, this implies the same cluster name would appear in two different groups.
TPA allows PEM to handle such inconsistencies rather than attempting to prevent them.
This generally means `deploy` will succeed but you may not get exactly the organisation of servers and agents you expected.
!!!

On instances with the `pem-server` role:

- `pem_server_group` specifies the name of the default group to which Postgres servers registered with this PEM Server will be assigned. If not specified it defaults to `PEM Server Directory`.
- `pem_agent_group` specifies the name of the default group to which PEM Agents registered with this PEM Server will be assigned. If not specified it defaults to `PEM Agents`

Note that the Postgres server and PEM Agent on the instance with `pem-server` role are always assigned to `pem_server_group` and `pem_agent_group` respectively.
TPA does not support adding this server or agent to a cluster.

## Shared PEM server

Some deployments may want to use a single PEM server for monitoring and
managing multiple clusters in the organization. Shared pem server deployment
within tpaexec is supported via the `pem_shared` variable that you could set via
`vars:` under the pem server instance for the given cluster config that plans
to use an existing pem server. `pem_shared` is a boolean variable so possible
values are true and false(default). When declaring a PEM server instance as
shared, we tell the given cluster config that the PEM server instance is in fact
managed by a separate cluster config that provisioned and deployed the pem
server in the first place. So any changes we wanted to make to the pem server
instance including postgres backend for pem would be managed by the cluster
where the PEM server instance is NOT declared as a shared pem instance.


A typical workflow for using a shared pem server across multiple clusters
would look something like this:

1. Create a tpaexec cluster with a single instance that has `pem-server`
   role (call it 'pem-cluster' for this example). We could as easily use
   the same workflow in a scenario where pem is provisioned as part of a
   larger cluster and not just a single instance that runs as the PEM server but
   we use a single node cluster because it is easier to use that as an example
   and arguably easy to maintain as well.
2. In the other cluster (pg-cluster for example), reference this particular
   PEM server from $clusters/pem-cluster as a shared pem server instance and
   use `bare` as platform so we are not trying to create a new PEM server instance.
   Also specify the IP address of the PEM server that this cluster can
   use to access the PEM server instance.

   ```yml
   - Name: my-pem-server
     node: 5
     role:
     - pem-server
     platform: bare
     public_ip: 13.213.53.205
     private_ip: 10.33.15.102
     vars:
       pem_shared: true
   ```
3. Before running deploy in the postgres cluster, make sure that pg-cluster
   can access pem server instance via ssh. You can allow this access by copying
   pg-cluster's public key to pem server instance via `ssh-copy-id` and then do
   an ssh to make sure you can login without having to specify the password.

   ```bash
   # add pem-clusters key to the ssh-agent (handy for `aws` platform)
   $ cd $clusters/pem-cluster
   $ ssh-add id_pem-clutser
   $ cd $clusters/pg-cluster
   $ ssh-keyscan -4 $pem-server-ip >> known_hosts
   $ ssh-copy-id -i id_pg-cluster.pub -o 'UserKnownHostsFile=tpa_known_hosts' $user@$pem-server-ip
   $ ssh -F ssh_config my-pem-server
   ```
4. Update postgresql config on pem server node so it allows connections
   from the new pg-cluster. You can modify existing pg_hba.conf on pem
   server by adding new entries to `pem_postgres_extra_hba_settings`
   under `vars:` in pem-cluster's config.yml. For example:

   ```yml
   instances:
   - Name: my-pem-server
     location: main
     node: 1
     role:
     - pem-server
     vars:
       pem_postgres_extra_hba_settings:
         - "# Allow pem connections from pg-cluster1.quire"
         - hostssl pem +pem_agent 10.33.15.108/32 cert
         - "# Allow pem connections from pg-cluster1.upside"
         - hostssl pem +pem_agent 10.33.15.104/32 cert
         - "# Allow pem connections from pg-cluster2.zippy"
         - hostssl pem +pem_agent 10.33.15.110/32 cert
         - "# Allow pem connections from pg-cluster2.utopic"
         - hostssl pem +pem_agent 10.33.15.109/32 cert
   ```

   and then run `tpaexec provision $clusters/pem-cluster` followed by
   `tpaexec deploy $clusters/pem-cluster`. When complete, nodes from
   your new pg-cluster should be able to speak with pem server backend.
5. In order to make sure pem agents from the nodes in pg-cluster can
   connect and register with the pem server backend, you must first
   `export EDB_PEM_CREDENTIALS_FILE=/path/to/pem/credentials/file`
   before you run `tpaexec deploy`. Credentials file is a text file that
   contains your access credentials to the PEM server's backend postgres
   instance in the `username:password` format.

   ```shell
   cat pem_creds
   ```
   ```output
   postgres:f1I%fw!QmWevdzw#EL#$Ulu1cWhg7&RT
   ```
   If you don't know the backend password, you can get that by using
    `show-password` tpaexec command.

   ```shell
   tpaexec show-password $pem-clusterdir $user
   ```


6. Run `tpaexec deploy $clusters/pg-cluster` so pem is deployed on the
   new pg-cluster while using shared pem server instance.

!!!Note Mixed-platform clusters
By declaring the shared PEM instance as `platform: bare` you
might have changed your cluster to a mixed-platform cluster. This may require
you to adjust other parts of `config.yml` to accommodate this change.
Specifically, the `instance_defaults` section must only contain settings
which are applicable to all instances in the cluster. If, for example,
your `instance_defaults` contains a setting such as `type` which is only
valid for `platform: aws` you must move that setting out of
`instance_defaults` and into only the instances which use the AWS platform.
!!!

## Connecting to the PEM UI

PEM UI runs on https interface so you can connect with a running
instance of PEM server via https://$pem-server-ip/pem. Login credentials
for PEM UI are set to the postgres backend user which uses `postgres`
or `enterprisedb` for `postgresql` and `epas` flavours respectively.
tpaexec's show-password command will show the password for the backend
user. For example:

```shell
tpaexec show-password $clusterdir $user
```

See [PEM documentation](https://www.enterprisedb.com/docs/pem/latest/)
for more details on PEM configuration and usage.

## Minor update for PEM using `tpaexec upgrade`

!!! Note PEM major version upgrades from version 9 to version 10.
    The PEM server package includes an SQL upgrade script which handles upgrading the database according to the PEM schema version.
    Upgrading from PEM `v9.8.0` to PEM `10.1.1` using `tpaexec upgrade` has been tested and works, but is a major version upgrade.
!!!

!!! Note PEM components are upgraded independently.
  Passing `pem-server` to `--components` upgrades ONLY the PEM server, whereas passing `pem-agent`
  upgrades ONLY the PEM agents.
  If upgrading separately, it is recommended to upgrade the agents before the server. When both are
  upgraded together, TPA upgrades the agents before the server.
!!!

When trying to upgrade the PEM agents to a specific package version, ensure the
`pem_agent_package_version` in `config.yml` is updated to reflect the desired version.

When trying to upgrade the PEM server to a specific package version, ensure the
`pem_server_package_version` in `config.yml` is updated to reflect the desired version.

The desired version can also be passed as an extra argument to the `tpaexec upgrade` command with:

```shell
tpaexec upgrade <cluster_dir> \
  -e pem_agent_package_version="<desired version>" \
  -e pem_server_package_version="<desired version>" \
  --components=pem-agent,pem-server
```

Refer to the section on
[package version selection and upgrade](tpaexec-upgrade.md#package-version-selection) for more
information.

To select PEM agents for upgrade, ensure the `--components` flag passed to the `tpaexec upgrade`
command contains `pem-agent` (or `all`)

To select the PEM server for upgrade, ensure the `--components` flag passed to the `tpaexec upgrade`
command contains `pem-server` (or `all`)

Refer to the section on [component selection for upgrade](tpaexec-upgrade.md#component-selection)
for more information.
