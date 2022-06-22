# Configuring Postgres Enterprise Manager (PEM)

TPAexec will install and configure PEM when `tpaexec configure` command
is run with `--enable-pem` command line option.

The default behavior with `--enable-pem` is to enable `pem-agent` role
for all `postgres` instances in the cluster. It would also add a dedicated
instance named `pemserver` to the cluster. Since PEM server uses postgres
backend; pemserver instance implicitly uses `postgres` role as well which
ensures that pemserver gets a valid postgres cluster configured for use
as PEM backend. All configuration options available for a normal postgres
instance are valid for PEM's backend postgres instance as well. See
following for details:

* [Configure pg_hba.conf](pg_hba.conf.md)
* [Configure postgresql.conf](postgresql.conf.md)

Note that PEM is only available via EDB's package repositories
and therefore requires a valid subscription.

## Supported architectures

PEM is supported with M1 and BDR-Always-ON architectures via
`--enable-pem` configuration command line option. You could optionally edit
the generated cluster config (config.yml) and assign or remove `pem-agent`
role from any postgres instance in the cluster in order to enable or
disable PEM there.

Note that PEM server does not support pgextended for a backend yet.

## PEM configuration

TPAexec will configure pem agents and pem server with the appropriate
instance-specific settings, with remaining settings set to the respective
default values. Some of the configuration options may be exposed for user
configuration at some point in future.

PEM server's web interface is configured to run on https and uses 443 port
for the same. PEM's webserver configuration uses self-signed certificates.

Default login credentials for PEM server web interface use the postgres
backend database user which is set to `postgres` for postgresql and
`enterprisedb` for EPAS clusters by default. You could get the login
password for the web interface by running
`tpaexec show-password $clusterdir $user`.

## Shared PEM server

Some deployments may want to use a single PEM sever for monitoring and
managing multiple clusters in the organization. Shared pem server deployment
within tpaexec is supported via `pem_shared` variable that you could set via
`vars:` under the pem server instance for the given cluster config that plans
to use an existing pem server. `pem_shared` is a boolean variable so possible
values are true and false(default). When declaring a pemserver instance as
shared, we tell the given cluster config that pemserver instance is in fact
managed by a separate cluster config that provisioned and deployed the pem
server in the first place. So any changes we wanted to make to the pem server
instance including postgres backend for pem would be managed by the cluster
where pemserver instance is NOT declared as a shared pem instance.


A typical workflow for using a shared pem server across multiple clusters
would look something like this:

1. Create a tpaexec cluster with a single instance that has `pem-server`
   role (call it 'pem-cluster' for this example). We could as easily use
   the same workflow in a scenario where pem is provisioned as part of a
   larger cluster and not just a single instance that runs as pemserver but
   we use a single node cluster because it is easier to use that as an example
   and arguably easy to maintain as well.
2. In the other cluster (pg-cluster for example), reference this particular
   pemserver from $clusters/pem-cluster as a shared pem server instance and
   use `bare` as platform so we are not trying to create a new pemserver instance.
   Also specify the IP address of the pemserver that this cluster can
   use to access pemserver instance.

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
   $ ssh -F ssh_config pemserver
   ```
4. Update postgresql config on pem server node so it allows connections
   from the new pg-cluster. You can modify existing pg_hba.conf on pem
   server by adding new entries to `pem_postgres_extra_hba_settings`
   under `vars:` in pem-cluster's config.yml. For example:

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

   and then run `tpaexec provision $clusters/pem-cluster` followed by
   `tpaexec deploy $clusters/pem-cluster`. When complete, nodes from
   your new pg-cluster should be able to speak with pem server backend.
5. In order to make sure pem agents from the nodes in pg-cluster can
   connect and register with the pem server backend, you must first
   `export EDB_PEM_CREDENTIALS_FILE=/path/to/pem/credentials/file`
   before you run `tpaexec deploy`. Credentials file is a text file that
   contains your access credentials to the pemserver's backend postgres
   instance in the `username:password` format.

   ```bash
   $ cat pem_creds
   postgres:f1I%fw!QmWevdzw#EL#$Ulu1cWhg7&RT
   ```
   If you don't know the backend password, you can get that by using
    `show-password` tpaexec command.

   ```bash
   tpaexec show-password $pem-clusterdir $user
   ```


6. Run `tpaexec deploy $clusters/pg-cluster` so pem is deployed on the
   new pg-cluster while using shared pem server instance.

## Connecting to the PEM UI

PEM UI runs on https interface so you can connect with a running
instance of PEM server via https://$pem-server-ip/pem. Login credentials
for PEM UI are set to the postgres backend user which uses `postgres`
or `enterprisedb` for `postgresql` and `epas` flavours respectively.
tpaexec's show-password command will show the password for the backend
user. For example:

```bash
tpaexec show-password $clusterdir $user
```

See [PEM documentation](https://www.enterprisedb.com/docs/pem/latest/)
for more details on PEM configuration and usage.
