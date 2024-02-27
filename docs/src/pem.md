# Configuring Postgres Enterprise Manager (PEM)

TPA installs and configures PEM when you run the `tpaexec configure` command 
with the `--enable-pem` command line option.

The default behavior with `--enable-pem` is to enable the pem-agent role for all
`postgres` instances in the cluster. The pem-agent role is also added to
Barman nodes when the `--enable-pg-backup-api` command line option is used
along with `--enable-pem`.

A dedicated instance named `pemserver` is also added to the cluster.

Since PEM server uses a Postgres backend, a `pemserver` instance implicitly uses the
postgres role as well, which ensures that `pemserver` gets a valid Postgres
cluster configured for use as a PEM backend. All configuration options available
for a normal Postgres instance are valid for PEM's backend Postgres instance
as well. For details, see:

* [Configure pg_hba.conf](pg_hba.conf.md)
* [Configure postgresql.conf](postgresql.conf.md)

PEM is available only by way of EDB's package repositories and therefore
requires a valid subscription.

## Supported architectures

PEM is supported with all architectures by way of the `--enable-pem`
configuration command-line option. An exception is the
BDR-Always-ON architecture when used with EDB Postgres Extended.
You can optionally edit the generated
cluster config file (`config.yml`) and assign or remove the pem-agent role from any
Postgres instance in the cluster to enable or disable PEM there.

## PEM configuration

TPA configures PEM agents and PEM server with the appropriate
instance-specific settings, with the remaining settings set to their
default values. Some of the configuration options might be exposed for user
configuration in the future.

PEM server's web interface is configured to run on https and uses port 443
for that configuration. PEM's web server configuration uses self-signed certificates.

The default login credentials for the PEM server web interface use the Postgres
backend database user, which is set to postgres for PostgreSQL and
enterprisedb for EDB Postgres Advanced Server clusters by default. You can get the login
password for the web interface by running
`tpaexec show-password $clusterdir $user`.

## Shared PEM server

Some deployments might want to use a single PEM server for monitoring and
managing multiple clusters in the organization. Shared PEM server deployment
in tpaexec is supported by way of the `pem_shared` variable. You can set this variable by way of
`vars:` under the PEM server instance for the given cluster config that plans
to use an existing PEM server. `pem_shared` is a Boolean variable, so possible
values are true and false (default). When declaring a PEM server instance as
shared, we tell the given cluster config that the PEM server instance is in fact
managed by a separate cluster config that provisioned and deployed the PEM
server in the first place. So any changes you want to make to the PEM server
instance, including the Postgres backend for PEM, are managed by the cluster
where the PEM server instance isn't declared as a shared PEM instance.

A typical workflow for using a shared PEM server across multiple clusters
looks something like this:

1. Create a tpaexec cluster with a single instance that has the pem-server
   role. (Call it `pem-cluster` for this example.) You can as easily use
   the same workflow in a scenario where PEM is provisioned as part of a
   larger cluster and not just a single instance that runs as a PEM server. 
   We use a single-node cluster because it's easier to use that as an example
   and arguably easy to maintain as well.
2. In the other cluster (`pg-cluster` for example), reference this particular
   PEM server from `$clusters/pem-cluster` as a shared PEM server instance. 
   Use `bare` as the platform so you aren't trying to create a new PEM server instance.
   Also, specify the IP address of the PEM server that this cluster can
   use to access the PEM server instance.

   ```yml
   - Name: pemserver
     node: 5
     role:
     - pem-server
     platform: bare
     public_ip: 13.213.53.205
     private_ip: 10.33.15.102
     vars:
       pem_shared: true
   ```
3. Before running deploy in the Postgres cluster, make sure that `pg-cluster`
   can access the PEM server instance by way of SSH. You can allow this access by copying the
   `pg-cluster` public key to the PEM server instance by way of `ssh-copy-id`. Then do
   an SSH to make sure you can log in without having to specify the password.

   ```bash
   # add pem-clusters key to the ssh-agent (handy for `aws` platform)
   $ cd $clusters/pem-cluster
   $ ssh-add id_pem-clutser
   $ cd $clusters/pg-cluster
   $ ssh-keyscan -4 $pem-server-ip >> known_hosts
   $ ssh-copy-id -i id_pg-cluster.pub -o 'UserKnownHostsFile=tpa_known_hosts' $user@$pem-server-ip
   $ ssh -F ssh_config pemserver
   ```
4. Update the PostgreSQL config file on the PEM server node so it allows connections
   from the new `pg-cluster`. You can modify the existing `pg_hba.conf` file on the PEM
   server by adding new entries to `pem_postgres_extra_hba_settings`
   under `vars:` in the `pem-cluster` `config.yml` file. For example:

   ```yml
   instances:
   - Name: pemserver
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

   Then run `tpaexec provision $clusters/pem-cluster` followed by
   `tpaexec deploy $clusters/pem-cluster`. When complete, nodes from
   your new `pg-cluster` can speak with the PEM server backend.
5. To ensure that PEM agents from the nodes in `pg-cluster` can
   connect and register with the PEM server backend, you must run
   `export EDB_PEM_CREDENTIALS_FILE=/path/to/pem/credentials/file`
   before you run `tpaexec deploy`. The credentials file is a text file that
   contains your access credentials to the PEM server's backend Postgres
   instance in the `username:password` format.

   ```bash
   $ cat pem_creds
   postgres:f1I%fw!QmWevdzw#EL#$Ulu1cWhg7&RT
   ```
   If you don't know the backend password, you can get that by using the tpaexec
    `show-password` command.

   ```bash
   tpaexec show-password $pem-clusterdir $user
   ```


6. Run `tpaexec deploy $clusters/pg-cluster` so PEM is deployed on the
   new `pg-cluster` while using the shared PEM server instance.

## Connecting to the PEM UI

The PEM UI runs on an https interface, so you can connect with a running
instance of a PEM server by way of https://$pem-server-ip/pem. Login credentials
for the PEM UI are set to the Postgres backend user that uses `postgres` for `postgresql`
or `enterprisedb` for `epas` flavors.
The tpaexec `show-password` command shows the password for the backend
user. For example:

```bash
tpaexec show-password $clusterdir $user
```

See the [PEM documentation](https://www.enterprisedb.com/docs/pem/latest/)
for more details on using and configuring PEM.
