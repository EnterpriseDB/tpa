# TPA release notes

© Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

## v23.38.0 (2025-06-02)

### Notable changes

- Make key_id/gpgkey optional in custom repository definitions

  The key_id and gpgkey parameters (for apt and yum custom repositories
  definition) are not required by the underlying modules, there are use
  cases where this is not easy to provide ahead of installation. With
  this change, TPA does not make it mandatory to provide those in custom
  repository definitions.

  References: TPA-882.

- Support for PGD6 architectures

  TPA can now configure and deploy clusters using the PGD-X and PGD-S
  architectures based on PGD6

  The PGD-S architecture implements PGD Essential and the PGD-X
  architecture implements PGD Expanded. These architectures have
  sensible default configurations and also accept various configure
  options to customise their behaviour.

  PGD 6 deployments no longer include pgd-proxy; instead, PGD's
  built-in Connection Manager is configured.

  Testing support for the new architectures is added.

  References: TPA-951, TPA-969, TPA-970, TPA-971, TPA-972, TPA-973, TPA-1010.

### Minor changes

- Add support for Rocky Linux 9 on AWS

  TPA now supports configuring a cluster using Rocky Linux 9.5
  on the aws platform. This is now the default version for
  Rocky Linux on aws if a version is not specified.

  References: TPA-968.

- Raise ArchitectureError for --network flag during configure

  By default, the Python standard library `ipaddress` package enforces
  'strict' interpretation of the CIDR, whereby the IP used should be
  the network address of the range.

  Previously, any IP passed to the `--network` flag that contained host
  bits would dump a stacktrace due to the raised ValueError. 

  That exception is now caught and an ArchitectureError is raised to
  display a clear message to the user about the `--network` parameter.

  References: TPA-910.

- Redirect pgbouncer to the new primary in M1 repmgr clusters during switchover

  Ensure that pgbouncer instances are redirected to the new primary node after using switchover command
  in a repmgr + pgbouncer cluster that has `repmgr_redirect_pgbouncer` set to true.

  tpaexec switchover command will now ensure that pgbouncer instance connect to the new primary node.

  a new `revert_redirect` variable can also be set as extra-variable after a first switchover is done
  to revert back to the initial primary node.

  References: TPA-941.

- Improve grant on barman_role

  Ensure the permissions for barman_role is idempotent and correctly uses
  bdr_database when in a bdr scenario with bdr initialized.

  Use postgresql_privs module to apply the grant on barman_role, so that
  changes are only applied when needed.

  Use the bdr_database on second deploys for BDR scenario. we want the DDL
  to be replicated accross the cluster, the recommended way is to let bdr
  do the replication and signal any change to the cluster as needed.

  References: TPA-1020.

- Document `cluster_vars` variable templating in config.yml

  Provide an explanation of correct templating procedure for variables
  defined under `cluster_vars` with a worked example in order to avoid
  confusion from unexpected behaviour associated with inventory variables
  not being defined when improperly templated in `config.yml`.

  References: TPA-1034, RT48797.

- Configure PEM to monitor Barman when both are present in a cluster

  When a cluster is configured with PEM enabled (using the --enable-pem
  option) and includes a Barman node, the following actions are now performed
  automatically:

  - `enable_pg_backup_api` is set to `true` in `config.yml`
  - The `pem-agent` role is assigned to the Barman node
  - The Barman endpoint is registered with the local PEM agent

  These changes simplify setup and ensure seamless integration between PEM and Barman.

  References: TPA-588.

- Add default value for EFM application.name property

  If the EFM application.name property is not set for a node, TPA
  will use a default of the postgresql cluster_name property. EFM
  uses this value when performing a switchover or when building
  a new standby database.

  References: TPA-1002.

- Skip repo checks when repo excluded from tasks

  The `repo` tag is available for exclusion, but previously would only
  skip tasks under the `sys/repositories` role. Now it also skips over
  the initialization tasks which check which repositories to use and 
  the verifies the credentials to access them are provided.

  References: TPA-959.

- Treat PEM_DB_PORT as a string for PEM 10.1 and above

  PEM 10.1 adds support for multi-host connection strings from the web
  application to the backend servers. To support this change, the PEM_DB_PORT
  parameter in PEM's `config_setup.py` file is now a string rather than an
  integer. While TPA does not yet support deploying HA PEM configurations,
  TPA will now correctly set this parameter as a string when the PEM version
  is 10.1 or greater.

  References: TPA-1009.

- Add a new tasks selectors `create_postgres_system_user` and `create_pgd_proxy_system_user`

  Add new task selectors that allow to skip the postgres_user and pgd_proxy_user operating system user.
  This allows clusters to use remote users created by a centralized user management such as
  NIS.

  This can be set in config.yml:

  ```
  cluster_vars:
    excluded_tasks:
      - create_postgres_system_user
      - create_pgd_proxy_system_user
  ```

  References: TPA-940, RT48601, RT44388.

- Fix verify-settings check in tpaexec test for pgd cli 5.7.0+

  The output for pgd cli command `pgd verify-settings` changed in 5.7.0
  TPA now correctly parses the output when using version above 5.7.0 of
  pgd cli.

  This is due to pgd commands overhaul, verify-settings will be deprecated
  along with other commands in future releases. those commands are now
  wrapper calling the new commands until the deprecation occurs.

  References: TPA-935.

- Added support for pg_backup_api on SLES 15

  Ensures pg_backup_api is correctly configured on SUSE Linux Enterprise Server 15 (SLES 15),
  when PEM monitoring is enabled and a Barman node is present in the cluster.

  References: TPA-1005.

- Improve behaviour of postgres_package_version

  Setting postgres_package_version will now cause TPA to install the
  selected version of various postgres-related components on Debian or
  Ubuntu systems installing EDB Postgres Advanced Server or EDB Postgres
  Extended Server. This avoids dependency resolution problems when newer
  package versions are visible in repositories.

  References: TPA-966.

- Use EDB repository setup script on SUSE

  Previously, we did not use the EDB repository setup script
  on SUSE because it did not work on repeat deploys. Zypper would
  raise because the repositories that the script attempts to install
  already exist, and require unique names.

  Now that the repository setup script task is skipped if the
  repositories are already installed, this issue is not encountered.

  References: TPA-974, TPA-633.

### Bugfixes

- Correctly merge ignore_slots in patroni config

  Fixed a bug whereby settings added to ignore_slots via
  cluster_vars['patroni_conf_settings']['bootstrap']['dcs'] were
  not merged into the eventual config.

  References: TPA-1016.

- Create `pgbouncer_get_auth()` function in dedicated database

  The `pgbouncer_get_auth()` function was created in the `pg_catalog`
  schema and execute granted to the `pgbouncer_auth_user`. This function 
  was created in every database, but this was not necessary for
  PgBouncer.

  A failure may be encountered during the `pgd node upgrade` process when
  this function was created in the `pg_catalog` schema as it is not 
  included in the dump created by `pg_dump`. A later task attempts to 
  run a `GRANT` on this function and fails, as the function is not
  restored since it was not originally dumped.

  Now this function is only created in a single database, named under
  the `pgbouncer_auth_database` variable in `config.yml`, which defaults to
  `pgbouncer_auth_database` if not included. It is only created if at
  least one instance with `pgbouncer` role is included in the cluster.

  A warning is also issued during deploy and upgrade if any databases
  define this function under the `pg_catalog` schema, as a future TPA
  release may remove the function from that schema.

  The `pgbouncer_get_auth()` function itself used by PgBouncer `auth_query` 
  has been updated to address `CVE-2025-2291`. This vulnerability allowed 
  for authentication using expired passwords, potentially granting 
  unauthorized access because the auth_query mechanism did not consider
  the `VALID UNTIL` attribute set in PostgreSQL for user passwords.

  References: TPA-382, RT42911, RT45068.

- Fix check mode when not using harp

  Fix the check mode for both deploy and upgrade when running a cluster
  without harp.
  the `Read current configuration file if exists` task needs to run in check mode
  to ensure we have the information available to correctly skip the following harp
  check task.
  shell module is by default skipped during check mode, we now let ansible know
  that this task has to be run.

  References: TPA-980.

- Skip raft checks for BDR nodes with replica role

  Physical replication of a `subscriber-only` node can be achieved in a `PGD`
  cluster by installing `repmgr` as a failover-manager and designating the
  `subscriber-only` node as the `primary` and listing another BDR data node 
  as the `backup`; this backup node is given the `replica` role.

  This configuration would result in the PGD upgrade process failing, since
  TPA expects BDR data nodes to have RAFT enabled, but the physical replica
  BDR data node (with both `replica` and `bdr` roles) by design does not.

  As a fix, certain BDR-specific tasks in the upgrade process now skip any node that 
  has a `replica` role, allowing for a successful upgrade.

  References: TPA-961, RT46186.

## v23.37.0 (2025-03-21)

### Notable changes

- Minor postgres upgrades for M1 + EFM clusters

  TPA can now upgrade postgres to the latest minor version on an M1 cluster
  which uses EFM as the failover manager.

  The upgrade process stops barman on any barman server in the cluster,
  then upgrades the replicas in the clusters.  Then it switches to one
  replica as a temporary primary, upgrades postgres on the original
  primary, and switches back to the original primary. The EFM agent
  is started and stopped on the different servers at the correct
  times. Then barman is restarted and cluster health checks are run.

  References: TPA-590.

- Improve minor postgres upgrade for M1 + repmgr clusters

  Improve minor upgrade of postgres in the context of M1 architecture
  along with repmgr as failover manager.

  Fixed missing upgrade of witness nodes. witness nodes were kept out of
  the process of upgrading, they are now upgraded along with replicas.

  Fixed postgres service restart to be more reliable and always run right
  after the package upgrade on the node is finished.

  References: TPA-898.

- Minor postgres upgrades for M1 + patroni clusters

  TPA can now upgrade postgres to the latest minor version on an M1
  cluster which uses patroni as the failover manager.

  The upgrade process stops barman on any barman server in the cluster,
  then upgrades the replicas in the cluster. Then it switches to one
  replica as a temporary primary, upgrades postgres on the original
  primary, and switches back to the original primary. Patroni's
  handling of the cluster is paused during the process and resumed
  afterwards. Then barman is restarted and cluster health checks
  are run.

  References: TPA-688.

### Minor changes

- Faster docker instance deprovision

  When deprovisioning docker instances, TPA now kills the container
  instead of stopping it, and does so to all the instances in parallel.

  References: TPA-903.

- Add check.num.sync.period property for EFM 5.x

  Starting with EFM 5.0, there is a new property 'check.num.sync.period'
  which defines how often a primary agent will check to see if num_sync
  needs to change on the primary database.

  References: TPA-960.

- Raise an ArchitectureError when BDR-Always-ON is configured with BDR version 5

  An architecture error is raised during `tpaexec configure` if
  `--bdr-version 5` is passed with `-a BDR-Always-ON` alerting
  the user that BDR version 5 should be used with `PGD-Always-ON`.

  References: TPA-742.

- Ensure URI for EDB repository setup is accessible

  The EDB repos are set up using the Cloudsmith setup script following
  the Cloudsmith documentation: piping the cURL output to bash for execution.

  However, if a user passes a nonexistent `EDB_SUBSCRIPTION_TOKEN` or repository
  to cURL, the exit code gets silently swallowed and replaced with a 0 because
  bash executes an empty input.

  A request is dispatched to a repository's GPG key endpoint to ensure a `404`
  response is not returned before continuing to download the setup script.

  Tasks related to EDB repository set up are now skipped if the repository has
  already been set up.

  References: TPA-939, TPA-689, TPA-633.

- Copy EFM config files if they are removed, even if no configuration changes

  If either the `efm.nodes` or `efm.properties` configuration files
  do not exist in the top-level EFM directory, the `efm upgrade-conf` 
  command copies them from the `/raw` directory, even if there have
  been no configuration changes. 

  This amends previous behavior that required a configuration change 
  before the `upgrade-conf` command would run and copy files.

  References: TPA-899.

- Create only required slots when configuring patroni

  When setting up a patroni cluster, a replication slot is created for 
  each etcd-only node. This causes problems because the unused slots cause 
  the WAL to accumulate. Slots are now only created for the DB servers.

  References: TPA-823.

- Separated changed from unchanged tasks in output

  In TPA's default output plugin, tasks which return "ok" but with
  no changes are now separated from ones that have reported changes,
  which are now highlighted in yellow.

  References: TPA-952.

### Bugfixes

- Pick the right upstream on EFM servers

  If a cluster is created with a pem-server, that backend is not
  monitored by EFM, hence, that node shouldn't be included when
  discovering a postgres primary for the entire cluster.

  References: TPA-929, RT45279.

- Fix shared_preload_libraries computing during deploy

  Fix a limitation from ansible's handling of list ordering that would
  trigger unneeded and uncontrolled rewritting of the
  shared_preload_libraries and subsequently require a postgres service
  restart, even on second deployment scenarios with no changes to the
  configuration.

  References: TPA-946.

- Fix duplicated lines in .pgpass files

  Fixed a bug whereby extra lines could be added to .pgpass for the same
  user when re-running 'tpaexec deploy'.

  References: TPA-928.

- Fix `patronictl switchover` command usage

  Patroni moved out from `master` naming some months ago
  TPA will now correctly use `--leader` instead of deprecated `--master`
  parameter when using `patronictl switchover` command.

  References: TPA-944.

- Count instances correctly in PEM clusters

  Fixed a bug whereby in certain circumstances, TPA would incorrectly
  calculate the number of instances in a BDR-Always-ON cluster with a
  PEM server, causing "tpaexec configure" to fail with "StopIteration".

  References: TPA-937.

## v23.36.0 (2025-02-19)

### Notable changes

- Use SLES15SP6 as the standard SLES for nodes

  When SLES is requested at configure-time, TPA will now install SLES15SP6.

  The docker and EC2 images are now SP6, and the systemd-sysvcompat package
  is installed on SLES, so that local boot-time scripts continue to work.

  References: TPA-901.

- Add support for Ubuntu Noble 24.04

  With this change, TPA is now able to create clusters locally and in AWS
  having ubuntu 24.04 as image.

  NOTE: Support will become effective when each software gets released for ubuntu 24.04. 
  Until then, Ubuntu 24.04 support is to be considered experimental.

  References: TPA-788.

- Bump Python dependency to version 3.12

  We were depending on Python 3.9, however, this release doesn't receive
  more updates and it's currently and finally discountinued.

  References: TPA-734.

### Minor changes

- Support EFM 5 "auto resume" properties

  Starting with efm 5.0, the auto.resume.period property has been
  broken into two properties, one for the startup case and one for
  the db failure case. This change adds the correct properties
  based on the efm_version being used.

  References: TPA-892.

- Fix Postgres database creation

  Starting with efm 5.0, a new property 'backup.wal' has been
  added. This change adds the new property if the version of
  efm is 5 or higher.

  References: TPA-893.

- Add `PGPORT` to the postgres user's `.bashrc` file installed by TPA

  The `PGPORT` environment variable has been exported as part of the 
  postgres user's `.bashrc` file. It defaults to the port value used by the 
  selected `postgres_flavour`, or `postgres_port` if specified in the config file.

  References: TPA-811.

- Wait for protocol version update during PGD upgrade

  During upgrade from PGD3 to PGD5, the protocol version uodate may take some
  time. The pgd5 specific config changes fail if they are attempted before
  protocl version change. Hence adding this wait to avoid such failures.

  References: TPA-904.

- Support package version specifiers for all cluster comppnents

  All components must be able to specify the package version in `config.yml` in
  order for `tpaexec upgrade` to support minor version upgrades so that the 
  desired version is known.

  The following software packages accept an `--xxx-package-version` option to the
  `tpaexec configure` command, which populates `xxx_package_version` in the generated
  `config.yml`

  - barman
  - pgbouncer
  - beacon-agent
  - etcd
  - patroni
  - pem-server
  - pem-agent
  - pg_backup_api
  - pgd_proxy
  - pgdcli
  - repmgr

  References: TPA-852, TPA-858, TPA-859, TPA-860, TPA-861, TPA-862, TPA-863, TPA-864, TPA-865, TPA-866, TPA-867, TPA-868.

- Use latest barman from PGDG on RedHat

  TPA previously defaulted to barman 3.9 when installing from PGDG on a
  RedHat-like system, as a workaround for broken packages. More recent
  barman packages are OK, so we now let yum install the latest packages.

  References: TPA-847.

- Set up EDB repositories via setup script for RedHat and Debian

  The repository manager provides a shell script that sets up the 
  desired EDB repositories.

  This simplifies EDB repository setup on TPA nodes into a single task.

  Currently it is only done for `dnf`/'yum' and `apt` package managers; the
  setup script was encountering an issue with `zypper` when the setup script
  is run on subsequent deploys.

  Due to this, SLES sets up EDB repositories without using the script.

  References: TPA-689.

- Fix documentation for `efm_conf_settings`

  Previously, documentation stated
  ```
  You can use efm_conf_settings to set any parameters, whether recognised by TPA or not. 

  Where needed, you need to quote the value exactly as it would appear in efm.properties
  ```

  However, the `efm.properties.j2` template uses the values from `efm_conf_settings` as an Ansible dictionary, 
  so the entries must be written in `key: value` form.

  ```yaml
  cluster_vars:
    efm_conf_settings:
      notification.level: WARNING
      ping.server.ip: <well known address in the network>
  ```

  References: TPA-886.

- Update `<clustername>.nodes` when new nodes are added to an existing EFM cluster

  When a new EFM node is added to `config.yml`, it is not listed in the 
  `Allowed node host list` on the existing EFM nodes in the cluster.

  The task which executes `efm upgrade-conf` and propagates the changes from
  `/raw/<clustername>.properties` and `/raw/<clustername>.nodes` is now run 
  when EITHER of these files are changed.

  This results in the new EFM node being written to the `<clustername>.nodes` 
  file and `efm cluster-status` including it in the `Allowed node host list`.

  References: TPA-848.

### Bugfixes

- Fix shared_preload_libraries on patroni clusters

  Entries in shared_preload libraries are now treated correctly by patroni.
  This fixes a bug whereby adding the pglogical extension to a patroni
  cluster via config.yml would fail.

  References: TPA-573.

- Deploys fail for distributions which have no additional repository setup commands for extensions

  When `postgis` is added to `extra_postgres_extensions` or the `extensions` 
  list of a database in `postgres_databases`, deploys fail for Debian,
  SLES and Ubuntu because their list of `repository_setup_commands` is
  empty (only RHEL has an additional command to run`crb enable`).

  This empty list of commands looped over and passed to the `command` module,
  which fails with `no command given`, resulting in deployment failure.

  As a result, the `Automatically run additional repository setup commands 
  for recognized extensions` task is now skipped if the distribution has
  no additional commands to run.

  References: TPA-771, TPA-885.

- Use standard form of home directory for etcd

  When creating the etcd user, TPA now refers to its home directory without
  a trailing slash, matching the usage of other tools like 'useradd'.

  References: TPA-907.

- Set `bdr_client_dsn_attributes` as the default for `pgd_proxy_dsn_attributes` and `pgd_cli_dsn_attributes`

  Because pgd-proxy and pgd-cli are written in Go and use a Go driver,
  they do not support the full set of parameter keywords supported by
  libpq.

  In the case a cluster has installed pgd-proxy and/or pgd-cli and has
  configured `bdr_client_dsn_attributes` with parameters that the Go
  driver does *not* support, two new configuration variables must be
  included: `pgd_proxy_dsn_attributes` and `pgd_cli_dsn_attributes`, 
  containing only additional DSN parameters that the Go driver
  supports.

  Conversely, if pgd-proxy and pgd-cli are installed and
  `bdr_client_dsn_attributes` does not include any Go-incompatible
  parameters, the connection strings for these tools will be configured
  with the attributes in `bdr_client_dsn_attributes`.

  This amends unexpected behavior where the `pgd_proxy_dsn_attributes`
  and `pgd_cli_dsn_attributes` were defaulting to empty strings when
  not defined, even though the user was expecting the parameters in 
  `bdr_client_dsn_attributes` to be used.

  References: TPA-897, TPA-820, RT44819.

- Fix Postgres database creation

  In order to remove modules (`CREATE EXTENSION` is not run, e.g. `pg_failover_slots`) 
  from the list of `extensions` specified for named databases under `postgres_databases`,
  the entire hash was modified. This introduced a bug, since a new hash was created
  that ONLY contained the database `name` and list of `extensions`, ignoring all other
  configuration settings for the database (`owner`, `template`, `encoding` etc).

  This resulted in databases being created with the default parameters rather than
  as configured.

  To fix this, the modules are removed from the list of extensions and the resulting
  list is passed to the task which runs CREATE EXTENSION.

  References: TPA-406, TPA-887.

- respect repmgr_use_slots when creating slots

  Fixed an issue whereby TPA attempted to create replication slots
  even when repmgr_use_slots was set to 0

  References: TPA-891.

- Add ssh port flag to Barman configuration

  The Barman configuration is now able to use custom ssh port set 
  via the `cluster_ssh_port` in `config.yml`, which defaults to
  22 if it is not set.

  The `-p`/`--port` flags are now included in the `ssh` command in
  `barman.d.conf` and `barman-wal-restore`/`barman-wal-archive' 
  commands respectively.

  References: TPA-900.

## v23.35.0 (2024-11-25)

### Notable changes

- Support PostgreSQL, EDB Postgres Extended, and EDB Postgres Advanced Server 17

  Clusters can be configured to use PostgreSQL, EDB Postgres Extended and 
  EDB Postgres Advanced Server version 17.

  Barman no longer needs to install the postgres server package to get 
  the `pg_receivewal` binary when using EDB Postgres Advanced Server 17 or 
  EDB Postgres Extended 17 since the binary has been added to the client 
  package for these versions.

  Raise an architecture error when a cluster is configured with `repmgr` 
  as the failover_manager as it is not available for Postgres 17.

  Updated documentation to reflect supported versions.

  References: TPA-803.

- Add new option when using etcd with HARP

  Add new optional var `harp_local_etcd_only` available when using etcd
  with HARP. This option tells HARP manager to connect to local etcd node.
  This recommendation follows the best practices learnt by doing the same
  when `bdr` as consensus procotol is being used.

  The default mode of adding multiple endpoints can lead to performance issues
  in some cases. This option is added to give more control to the user.

  References: TPA-821.

- Support STIG/CIS compliance

  TPA now supports command-line options to create a cluster configured
  to conform to many of the requirements of the STIG and CIS security
  standards.

  These options cause TPA to set many postgresql.conf settings as
  defined in the relevant standards, to install required extensions,
  to configure other aspects of system behaviour such as filesystem
  permissions and user connection limits, and to check for other
  requirements such as FIPS crypto standards which TPA can't directly
  impose.

  The clusters thus generated are not certified by TPA to conform to
  the standards, but much of the groundwork of creating a conforming
  cluster is now automated.

  References: TPA-366, TPA-836, TPA-837.

- Add support for PGD Lightweight architecture

  TPA is now able to generate a PGD Lightweight architecture comprised of
  three nodes in two locations (2 nodes in Primary and one in Disaster
  Recovery) designed to ease migrations from physical replication.

  Users can now run `tpaexec configure lw -a Lightweight --postgresql 15`.

  References: TPA-838.

- Have `configure` create a user-defined network on docker

  The configure command will now automatically add a named network and static IP addresses to config.yml
  when Docker is the selected platform.

  The network name is the same as the cluster name and the address range follows the existing semantics of the
  --network option with the exception that only one subnet is used for the whole cluster rather than one per
  location. If a subnet prefix is not specified by the user, TPA will attempt to select a prefix which results
  in a subnet large enough to fit the whole cluster.

  The key `ip_address` may now be used to specify a static IP for a Docker instance as long as a named network
  is specified in the config.yml.

  References: TPA-261, TPA-407, TPA-434.

### Minor changes

- Support RedHat Enterprise Linux 9 for ARM architectures

  Packages are now published targeting RHEL 9 ARM64, and TPA should support
  deployments using this architecture and OS.
  Also updated the list of supported AWS images to include the RedHat 9
  ARM64 AMI provided by Amazon.
  The default `instance_type` for ARM64 EC2 instances has been updated
  from `a1` to `t4g`, which is the current generation processor available
  for burstable general purpose workloads.

  References: TPA-780.

- Added experimental support for using an existing Barman node as backup node in new cluster

  When using an existing Barman node as a backup node in a new cluster, users
  can set `barman_shared: true` in the Barman instance's vars with the platform
  set to `bare` and other information supplied as usual for bare instances.

  This change allows TPA to skip some configuration steps that would
  otherwise fail due to usermod issues, as the Barman user already has
  running processes from previous deployments.

  The shared Barman instance is treated as a bare instance, so the required
  access, including the Barman user's access to the target PostgreSQL
  instances, must be already in place. Copying the Barman user's keys from
  the original cluster to the new cluster can be used to achieve this, 
  see the Barman section of the TPA documentation for detailed information.

  References: TPA-777, RT37792.

- Only add nodes with `efm` role to cluster `efm.nodes` file

  A support ticket questioned why the `pemserver` and `barman` nodes are
  added to the `Allowed node host list` in EFM when they are not 
  relevant to EFM functions. Refactored the task that writes the `efm.node`
  configuration to only include those nodes that have `efm` in their list 
  of roles.

  References: TPA-817, RT40645.

- Remove deprecated `PermissionStartOnly` in postgres.service.j2 template

  `PermissionsStartOnly` has been deprecated and is now achieved via 
  `ExecStartPost=+/bin/bash...` syntax

  References: TPA-762.

- Improve postgres-monitor script

  Improve postgres-monitor script to better manage recoverable errors and
  add retries on network errors to ensure that it won't return failure when
  it just didn't allow enough time for postgres service to  be fully started.

  References: TPA-796, RT39191.

- Enable EFM probes when a PEM agent is registered on an EFM node

  The `--efm-install-path` and `--efm-cluster-name` flags are set when a 
  PEM server is registered on an EFM node. 

  The `Streaming Replication`, `Failover Manager Node Status` and 
  `Failover Manager Cluster Info` probes are enabled when a PEM agent is 
  registered on an EFM node.

  References: TPA-586.

- The `barman` Postgres user should not be a superuser

  Certain required privileges are granted to Postgres role, `barman_role`, which is
  then granted to the `barman` Postgres user. This avoids creating the `barman`
  user as a superuser. This role can also be granted to other Postgres users
  by adding it to their `granted_roles` list using `postgres/createuser`.

  The `barman_role` is created as part of the Barman tasks; if Barman is not
  used, this role will not be created. Therefore, the task that grants privileges
  to this role is only executed if the `barman_role` username is in the list 
  of Postgres users that are created.

  The 'barman' user now has `NOSUPERUSER` explicitly specified as a role attribute. 
  If a cluster was deployed with a previous TPA version (which created the 'barman' 
  user as a superuser), deploying with this version will remove the `superuser`
  role attribute from the `barman` user.

  References: TPA-148, TPA-818.

- Add `postgis` to list of recognized extensions

  The PostGIS package will automatically be added when a user specifies 
  `postgis` as an entry in either `postgres_extensions` or the list of
  extensions named under `postgres_databases`.

  Also enables the CRB (Code Ready Builder) repository for RHEL-compatible
  distributions so PostGIS dependencies can be installed.

  References: TPA-771.

- Allow multiple addresses to be supplied with hostnames

  When using the `--hostnames-from` option to `tpaexec configure`, you
  can now include two ip addresses on each line, which will be included
  in the generated config.yml as public_ip and private_ip.

  References: TPA-841.

- Make `password_encryption` algorithm for `efm` Postgres user configurable.

  Expose a configurable `efm_user_password_encryption` variable which should
  be set to either `'md5'` or `'scram-sha-256'` depending on user requirements.
  This controls the `auth-method` for the `efm` Postgres user in `pg_hba.conf` 
  and the algorithm used for generating it's encrypted password.

  In clusters deployed with `compliance` configured to `stig`, the 'efm' Postgres
  user's `auth-method` in `pg_hba.conf` will be set to `scram-sha-256` since 
  FIPS-enabled operating systems do not allow `md5` to be used.

  References: TPA-832, TPA-836.

### Bugfixes

- set pem_python_executable outside pkg role

  Fixed a bug whereby if the user excluded the `pkg` selector, later
  pem-related tasks would fail because the pem_python_executable fact
  had not been set.

  References: TPA-814.

- `primary_slot_name` added for EFM compatibility interferes with `bdr_init_physical`

  Previously, the `primary_slot_name` configuration task runs when the
  `failover_manager` is NOT `repmgr`; both `efm` and `patroni` 
  use `pg_basebackup` which, unlike `repmgr`, does not configure a 
  `primary_slot_name` on the primary node when creating a replica.
  This is to ensure the old primary uses a physical slot for replication 
  during a switchover.

  However, this also caused the task to run when the `failover_manager` is `bdr`.
  When `bdr_init_physical` was used on PGD cluster nodes, initialisation failed 
  because it used a non-existent slot.

  This is fixed by conditionally running the task which configures the `primary_slot_name` 
  when the `failover_manager` is explicitly `efm` or `patroni` to avoid setting it unnecessarily.

  References: TPA-712, TPA-825, RT36064.

- Clear error message stack after each task

  Fixed an issue whereby in some cases error messages would be repeated
  even after successful tasks.

  References: TPA-812.

- Fix tpaexec test for pgd-proxy config verification

  Fixed a bug whereby the test that ensures the current pgd-proxy configuration
  matches the expected configuration would fail for version < 5.5.0. This fix
  ensures that TPA won't try to query configuration keys added in version 5.5.0.

  References: TPA-819.

- Enable new replicas in patroni clusters

  Fixed an issue whereby new replicas in patroni clusters would fail
  with errors related to replication slots.

  References: TPA-792, TPA-781.

- Add `pem-agent` role on barman nodes at most once for M1 architecture

  If `--enable-pem` and `--enable-pg-backup-api` are passed to `tpaexec configure`,
  `pem-agent` is added twice to the `barman` node if it is also a `witness`. 
  Fixed by by consolidating both `if` statements together to only evaluate 
  the conditions once.

  References: TPA-793.

- Download correct `bash-completion` package version

  If the `pgdcli_package_version` is specified in `config.yml`, the 
  `bash-completion` package is incorrectly named because the 
  `packages_for` filter erroneously appends the `pgdcli_package_version` 
  to the  package name. This results in an attempt to download a nonexistant
  package.

  The `bash-completion` package is now appended to the list after the
  `packages_for` filter, since it's version is independent from the 
  `pgdcli_package_version`.

  References: TPA-794, RT38773.

## v23.34.1 (2024-09-10)

### Bugfixes

- Running deploy after a switchover fails for nodes with `efm-witness` role

  The `upstream-primary` for EFM nodes is determined using the facts
  gathered from Postgres. This fails for nodes with `efm-witness` roles 
  since they do not have Postgres. The task to determine upstream-primary 
  is now run only on nodes with `primary` or `replica` roles

  References: TPA-580, TPA-789, TPA-798.

## v23.34 (2024-08-21)

### Notable changes

- Allow cert authentication on pgbouncer

  pgbouncer can now use cert authentication when connecting to its
  postgres backend. This is particularly useful with FIPS; it's
  required because the authentication algorithm is also changed, from
  md5 to scram-sha-256. The variable
  `pgbouncer_use_cert_authentication` must be defined to true in
  cluster_vars, should someone decide to enable this mode. When this
  mode is enabled, TPA will create a CA and two more certificates
  replacing the self-signed certificate created by default in all
  clusters.

  Change requires a postgres restart.

  References: TPA-650.

- Remove support for Raid volume creation on AWS

  TPA no longer supports RAID creation on AWS. All EBS volumes are automatically
  replicated across different servers which might be seen as redundant if during
  or before boot, a RAID device is provisioned. If anyone despite this level of
  default availability provided by AWS still requires a form of software RAID,
  the device must be created manually and configured to be used by TPA afterwards.

  References: TPA-13.

- Change default output to TPA's own format

  Ansible's default output plugin shows a lot of information, much of
  which is useful when debugging but obscures the flow of information if
  you just want to see what TPA is doing. TPA now has its own output
  plugin, which shows one line of information per task, omitting tasks
  for which even one line would be uninformative. The lines are indented
  to enable TPA's control flow to be visible, and include colour-coded
  counts of successful, skipped, and ignored hosts.

  The fuller output can be turned on by setting TPA_USE_DEFAULT_OUTPUT=true
  in your environment, or by adding the -v switch to the command line.

  References: TPA-673, TPA-778.

### Minor changes

- Run efm upgrade-conf on new clusters

  Run the efm upgrade-conf on new cluster deployments to benefit
  from the comments and inline documentation that are added to
  both <cluster_name>.properties and <cluster_name>.nodes files.

  References: TPA-707.

- Add efm-pre-config hook

  The efm-pre-config hook runs after efm has been installed and its
  configuration directory and user have been created, but before efm is
  configured. It can be used to install custom efm helper scripts.

  References: TPA-791.

- Add support for passing options to register PEM agent

  Additional options can be included when registering PEM agents by
  listing them under `pemagent_registration_opts` in `cluster_vars`.

  References: TPA-584.

- Update upstream_primary after switchover

  The `upstream_primary` is now correctly updated after switchover, 
  resulting in the correct `auto.reconfigure` setting be set on replicas.
  Standbys now follow the new primary.

  References: TPA-580.

- Allow customer's to use their own SSL certificates on the PEM server

  Users can include the names of the certificate and key pair for use on the PEM server in `config.yml`
  under the cluster_vars or pem-server instance vars `pem_server_ssl_certificate` and `pem_server_ssl_key`.
  TPA will copy them from the `ssl/pemserver` directory of the cluster directory to the PEM server and 
  configure Apache/httpd accordingly.

  References: TPA-718, TPA-752, RT35811.

- Add missing properties to efm template

  Add properties that are present in EFM 4.9 that were not in the
  template already:

  enable.stop.cluster: boolean, default true
  priority.standbys: default ''
  detach.on.agent.failure: boolean, default false
  pid.dir: default ''

  On existing clusters, since this means a change in the EFM
  configuration, TPA will restart EFM services to make sure changes
  are applied.

  EFM agents only process the properties that they know about, so if
  the new properties are written out for an older version of EFM that
  does not use them, they will be ignored.

  References: TPA-776.

- Enable efm to use hostname instead of IP address as `bind.address`

  Add a new configure option to let efm setup the cluster using hostname
  resolution instead of IP addresses for `bind.address` value.

  Introduce `--efm-bind-by-hostname` for architecture M1 configure command and
  `efm_bind_by_hostname: true|false` in cluster_vars  section of config.yml.
  Defaults to `false` when omitted.

  References: TPA-758.

- Remove EFM dependency for resolving upstream_primary

  Previously, EFM was queried for the current primary on a deploy after 
  a switchover. If EFM is not running, this will fail. 
  Now the cluster_facts collected through Postgres are used to determine 
  the current primary after a switchover, removing the dependency on EFM.

  References: TPA-789, TPA-580.

### Bugfixes

- Fixed an issue when backing up from a replica

  When taking backups from a replica, barman could fail when taking its
  initial backup by timing out waiting for WAL files. This is fixed by
  waiting for barman to complete its base backup before forcing a WAL
  segment switch.

  References: TPA-719.

- Ensure we flush handlers soon after finishing postgres configuration

  This problem manifested itself when a new node was added to a repmgr
  or efm cluster, TPA would fail to reload/restart postgres on
  existing nodes to re-read configuration changes and the new node
  would therefore fail to connect to the cluster.

  References: TPA-781.

- Ignore proxy settings when accessing the Patroni API

  The Ansible default is to use a proxy, if defined. This does not
  work in the (rather common) case of an airgapped environment that
  needs a proxy to download packages from the internet, because the
  proxy also intercepts (and disrupts) calls to the Patroni API.

  References: TPA-790.

- Set appropriate PEM agent parameters monitored servers

  TPA broadly sets PEM agent parameters on all instances that are only 
  appropriate for the pemserver instance. This is fixed by conditionally
  setting parameters in `agent.cfg.j2` based on whether or not the node 
  is a pem-server.

  References: TPA-744.

- Fix incorrect detection of cgroup data

  Fix two cases of incorrect cgroup detection:
    - on MacOSX, we no longer try to read /proc/mounts
    - on systems where /sys/fs/cgroup is ro but mounts under it are rw, we
      now correctly detect this

  References: TPA-760.

- Fix missing pgd-proxy and pgdcli package name for SLES

  Add missing entries for pgd-proxy and pgdcli default package name when
  using SLES operating system as target for cluster nodes.

  References: TPA-768.

- Fix witness node registration to repmgr

  Ensure that `repmgr witness register` command is used with the correct postgres_port value
  even when using non-default postgres port for the upstream_primary postgres.

  References: TPA-772.

- Honour failover_manager when overriden at instance level for PGD instances

  Allow failover_manager override to `repmgr` to work correctly when
  set at instance level for subscriber-only nodes and their replicas
  in PGD clusters.

  References: TPA-767.

- Fix tpaexec test for pgd-proxy read_listen_port check

  Ensure we can verify the actual config set on pgd-proxy nodes for the newly added
  `read_listen_port` option in pgd-proxy.

  References: TPA-775.

- Explicitly install packages for PEM web server

  PEM 9.7.0 no longer depends on Apache at a package level therefore
  to use Apache as the web server we install the packages explicitly.
  This prevents deploy failing with PEM 9.7.0 or later.

  References: TPA-795.

## 23.33 (2024-06-24)

### Notable changes

- Add support for ARM64 in Debian 12 (Bookworm)

  This debian version is the first in its kind to receive full EDB support
  on arm64 devices.

  References: TPA-528.

### Minor changes

- Change haproxy_bind_address when Patroni is failover_manager

  The default value of `haproxy_bind_address` (`127.0.0.1`) does not allow for
  communication between Postgres nodes and haproxy nodes. 
  The bind address is now set to `0.0.0.0` when Patroni is the failover manager.
  Users should change this value to something more restrictive and 
  appropriate for their cluster networking.

  References: TPA-720.

- Basic integration between Patroni and PgBouncer

  The `--enable-pgbouncer` option of `tpaexec configure` is made available so
  users can easily create a cluster with PgBouncer. When given through the
  command-line, TPA will add the `pgbouncer` role to the Postgres hosts and
  configure PgBouncer to pool connections for the primary node.

  When adding PgBouncer nodes in a Patroni enabled cluster, TPA
  configures Patroni with a `on_role_change` callback. That callback takes
  care of updating the primary connection info in the PgBouncer nodes in
  response to failover and switchover events.

  References: TPA-754.

- Various task selection fixes

  Task selectors are now consistently applied in the final stage of
  deployment. Consistency of task selectors in the tests is improved
  and the examples of task selectors in the docs are now correct.

  All deploy-time hooks now have corresponding task selectors.

  References: TPA-713.

- Support configuring read-only endpoints on PGD proxy nodes

  PGD version 5.5 allows for proxy nodes to be configured as read endpoints, 
  which direct read-only queries to a shadow node. TPA supports this configuration 
  option by setting a `read_listen_port` parameter under `default_pgd_proxy_options` 
  and `pgd_proxy_options` in `config.yml`. This parameter is included by default when 
  the PGD version is >= 5.5. 

  Users can also specify the port numbers by passing `--proxy-listen-port` 
  and `proxy-read-listen-port` arguments to the `tpaexec configure` command.

  References: TPA-722.

- Make barman-cli package subject to barman_package_version

  If barman_package_version is set, TPA will now look at it when looking
  for the barman-cli package as well as for barman itself. This resolves
  an inconsistency which caused clusters using the downloader to fail when
  barman_package_version was used.

  References: TPA-749.

- Force barman 3.9 when installing rpms from PGDG

  To work around broken barman 3.10 packages in the PGDG repos, TPA
  now installs version 3.9 of barman if using PGDG repos on an
  RHEL-family system. This behaviour can be overridden by explicitly
  setting barman_package_version in config.yml .

  References: TPA-750.

- Add support for `postgres_wal_dir` in Patroni deployments

  When a custom `postgres_wal_dir` is specified in TPA configuration, TPA will
  make sure to relay that option to the corresponding settings in the Patroni
  configuration file.

  That way, if Patroni ever needs to rebuild a standby on its own, out of TPA,
  the standby will be properly set up with a custom WAL directory.

  References: TPA-741.

- Allow the user to choose between `edb-patroni` and `patroni` packages

  EDB now produces its own `edb-patroni` package instead of rebuilding the
  `patroni` packages from PGDG. As a consequence, TPA was changed to allow
  users to select between `patroni` and `edb-patroni` packages.

  The selection is made through the new TPA setting `patroni_package_flavour`,
  which can have one among the following values:

  * `edb`: Install `edb-patroni` (using EDB repositories). This requires the
    user to configure `edb_repositories` TPA setting;
  * `community`: Install `patroni` package (using PGDG repositories). This
     requires the user to configure `PGDG` repository in either
     `apt_repository_list`, `yum_repository_list` or `suse_repository_list`
     TPA settings, depending on the target operating system.

  Note that you can change the package flavour at any time. TPA is able to
  transparently migrate between flavours. You only need to make sure the
  appropriate repositories are configured.

  For TPA clusters which have no `patroni_package_flavour` set in the
  configuration file, TPA will attempt to infere the flavour based on the
  configured repositories. If EDB repos are configured, `edb` flavour is
  assumed, otherwise `community` flavour.

  References: TPA-725.

### Bugfixes

- Fixed an issue whereby docker provisioning failed with "read-only file system"

  On host systems running cgroup1 with docker containers running recent
  OS images, `tpaexec provision` could fail to provision containers
  with an error message like "mkdir /sys/fs/cgroup/tpa.scope: read-only
  file system". TPA will now detect this case and avoid it.

  References: TPA-740.

- Clear error message when running cmd or ping before provision

  References: TPA-733.

- Fixed permissions for harp dcs user

  Fixed an issue whereby required permissions on functions in the bdr database
  were not being granted to the harp dcs user on a witness node.

  References: TPA-746.

## v23.32 (2024-05-14)

### Notable changes

- Flexible M1 architecture

  The M1 architecture now supports the following additional arguments to
  `tpaexec configure`:

  --location-names
  --primary-location
  --data-nodes-per-location
  --witness-only-location
  --single-node-location

  By combining these arguments, various layouts can be specified.

  References: TPA-333.

- Add support for Debian 12 x86

  Now it's posible to enjoy tpaexec packages for bookworm but also create
  and manage clusters in either docker and AWS.

  References: TPA-717.

- Introduce support for ppc64le

  Customers running on ppc64 infrastructure can now install and use tpaexec
  directly from our packages. Thanks to this new advance, the gap between
  x86_64 and ppc64le regarding accessibility of software has been reduced.

  References: TPA-675.

- Support cgroups v2 systems for the docker platform

  TPA can now provision docker clusters on hosts running cgroups 2,
  for all systems except RHEL 7. On newer systems (RHEL 9 or Ubuntu 22.04),
  TPA will use cgroups 2 scopes for additional isolation between the host
  and the containers.

  References: TPA-441.

### Minor changes

- Document instructions for creating an Execution Environment (EE)

  TPA version 23.30 introduced the support for Ansible Automation
  Platform (AAP) version 2.4. This version of AAP makes use of EE to
  run ansible playbooks. This change includes updates to the tower/AAP
  documentation to include instructions on creating your own EE.

  References: TPA-708.

- Add useful extensions by default when role is pem-agent

  The `sql_profiler`, `edb_wait_states` and `query_advisor` extensions
  are automatically included for any `pem-agent` node.

  The list of default extensions for pem-agent nodes is overridable by
  including a list of `pemagent_extensions` in config.yml.

  If this list is empty, no extensions will be automatically included.

  References: TPA-336.

- Update AWS AMI versions

  AWS AMI versions for certain distributions will be out of date, so each
  supported AMI was updated to the latest version.

  References: TPA-710.

- Install chrony NTP service by default

  TPA will install chrony during deploy now keeping the default config upon
  all except on AWS where we point to Amazon Time Sync service.

  References: TPA-93.

- Add --force option to `tpaexec relink`

  By default, relink doesn't modify targeted files if they already
  exist. With --force, relink removes all existing targeted files then
  recreates them.

  --force is needed to update AAP-enabled cluster directories after
  TPA package upgrade and is also useful for rescuing a cluster that
  has been broken by manual intervention.

  References: TPA-706.

- Add `pg_failover_slots` to recognized extensions

  pg_failover_slots is a module, so CREATE EXTENSION cannot be run
  for its entry in either `postgres_extensions` or the list of
  extensions named under `postgres_databases`.

  A key-value pair of `module: true` is included with its entry in the
  `default_postgres_extensions_dictionary`.

  Logic is added to construct a list of extensions flagged `module`
  and remove the entries from the `postgres_extensions` and extensions
  under `postgres_databases` if necessary.

  The required package and shared_preload_library entry are included and
  CREATE EXTENSION is not run for `pg_failover_slots`.

  References: TPA-406.

- Add ip_address to the ip_addresses list

  If the key `ip_address` is defined for a node, add a corresponding entry
  to `ip_addresses`. This ensures that TPA can correctly work out whether
  streaming is working correctly when re-running deploy on an existing cluster.

  This fixes error messages like "Unrecognised host=10.136.4.247 in
  primary_conninfo" for nodes with `ip_address` defined.

  References: TPA-711, RT103488.

- Use archive.debian.org to get buster backports on aws

  The backports repository for debian 10 (buster) is no longer available
  on deb.debian.org but the standard AWS AMI still refers to it, so we
  modify /etc/apt/sources.list accordingly before attempting apt operations.

  References: TPA-715.

- Prevent deployment failing on AWS when `assign_public_ip:no` is set

  When AWS was selected as platform and `assign_public_ip` was set to no,
  there were some cases where tpa was still looking for a public IP. This
  change now prevents that.

  References: TPA-666.

- Change to sourcedir when compiling BDR from source

  Move to the location where the source code has been downloaded
  before compiling BDR instead of using a relative path.
  This decreases the chances of picking a wrong Makefile or worse,
  ending in a broken path.

  References: TPA-153.


### Bugfixes

- Suppressed 2q token error message

  Fixed an issue whereby an error would be raised if the user had an
  expired subscription token for 2q repositories, even if their
  configuration didn't use those repositories.

  References: TPA-705.

- Fix formatting of `line` option for `lineinfile` command

  The task was skipped because the command was incorrectly formatted,
  resulting in the restore_command override not being removed from
  `postgresql.auto.conf`

  References: TPA-691.

- Fix problems with custom barman and postgres users

  Fixed problems with various roles that caused mixed errors when
  trying to use custom users for barman and postgres, thereby
  resulting in a failed deployment.

  References: TPA-704, TPA-151.

- Fix relink error when upgrading

  Fixed an error whereby `tpaexec upgrade` could invoke the relink
  script in a way which caused an error and showed an unhelpful usage
  message for `tpaexec relink`.

  References: TPA-721.

## 23.31 (2024-03-19)

### Bugfixes

- Fix errors in conditionals

  Fixes to syntax errors in some conditionals which could stop a deploy
  from running.

  References: TPA-702.

## v23.30 (2024-03-19)

### Notable changes

- Remove support for ansible versions less than 8

  Ansible 2.9 is no longer supported, neither as the community
  distribution nor as the 2ndQuadrant fork.
  Please note that, per the previously issued deprecation notice,
  this release completely removes support for 2ndQuadrant Ansible,
  which is no longer maintained. In addition, after Ansible 8 became
  the default in version 23.29, this version requires Ansible 8 or
  newer. To ensure you have a compatible Ansible version, please run
  tpaexec setup after updating TPA as detailed in the documentation.

  Users who have been using the `--skip-tags` option to `tpaexec
  deploy` should move to the new `--excluded_tasks` option.

  References: TPA-501, TPA-686.

- Generate an Execution Environment image for Ansible Automation Platform support

  TPA now generates a custom Execution Environment docker image to be
  used in Ansible Automation Platform 2.4+ (Controller version 4+).
  This image contains everything needed to run deployments via AAP.
  This image is built using ansible-builder and either redhat
  ee-minimal-rhel9 image or a python-alpine lightweight base image.

  References: TPA-679, TPA-680, TPA-682.

- Task selectors replace ansible tags

  Selective execution of tasks is now supported using custom selectors
  rather than ansible tags.

  To run only tasks matching a certain selector:

    tpaexec deploy . --included_tasks=barman

  To skip tasks matching a certain selector:

    tpaexec deploy . --excluded_tasks=ssh

  Task selectors can also be used by specifying the `excluded_tasks` or
  `included_tasks` variables in config.yml .

  References: TPA-657.

### Minor changes

- Improve extension configuration

  Automatically handles adding package names and shared preload
  library entries for a subset of extensions.

  For these specific extensions, only the extension name is needed in
  the `extra_postgres_extensions` list or the the `extensions` list of
  a database entry in `postgres_databases`.

  References: TPA-388, TPA-293.

- Add `bluefin` to list of recognized extensions

  The EDB Advanced Storage Pack package and shared preload library
  entry will automatically be added for `bluefin` when a user
  specifies it as an extension and the `postgres_version` is 15 or
  greater.

  References: TPA-307.

- Avoid synchronizing database structure to PGD witness nodes

  Currently, when creating a witness node, PGD will by default synchronize
  the source node's database structure. This is however not necessary
  and the synchronized schema will never be used or updated. To prevent
  this happening, explicitly set bdr.join_node_group()'s option
  "synchronize_structure" to "none" for witness nodes.

  References: TPA-665.

- Add option to provision without deploying

  If an instance has `provision_only: true` in config.yml, it will
  be provisioned as normal but not added to the inventory which is seen
  by `tpaexec deploy`.

  An example use for this is with a custom docker image to set up a
  testing environment.

  References: TPA-627.

### Bugfixes

- Fix preloads that differ from their extension name

  Addressed by TPA-388, the `default_postgres_extensions_dictionary`
  contains the correct shared preload library entry name for each
  extension.

  References: TPA-645.

## v23.29 (2024-02-15)

### Notable changes

- Support choosing Ansible version

  The `--ansible-version` argument to `tpaexec setup` now accepts `8` or `9`
  as valid ansible versions, as well as the existing `2q` or `community`, both
  of which imply ansible 2.9. The default is now `8`.

  Support for ansible 9 is experimental and requires python 3.10 or above.

  References: TPA-646.

- Support Keyring for cluster vault password storage

  Add support for system keyring to store cluster vault password by
  default. This leverages python keyring module to store vault
  password in the supported system keyring when `keyring_backend` is
  set to `system` (default for new clusters). This change does not
  impact existing clusters or any clusters that set `keyring_backend`
  to `legacy` in config.yml. `vault_name` setting in config.yml is
  used in combination with `cluster_name` to ensure uniqueness to
  allow provisioning for multiple clusters that all use the same
  `cluster_name` setting. Refer to tpaexec-configure.md for details.

  References: TPA-85.

### Minor changes

- Fix edb_repositories generated by reconfigure

  Ensure that edb_repositories already defined in config.yml are kept during reconfigure
  especially now that all cluster will use edb_repositories by default. Fixes bdr4 to pgd5
  upgrade scenario in air gapped environment.

  References: TPA-660.

### Bugfixes

- Improve error recognition in postgres-monitor

  postgres-monitor will now recognise the message "the database system is
  not yet accepting connections" as a recoverable error.

  References: TPA-658.

- Skip postgres/config/final role on replicas when upgrading

  References: TPA-639.

- Respect package versions in the downloader

  When using the downloader on a Debian-family system, we now perform our
  own fnmatch-style globbing on any package versions specified in
  config.yml, enabling constructions like `bdr_package_version: 4:5.0.*`
  to behave in the same way as when the downloader is not in use.

  References: TPA-583.

- Ensure that the downloader gets latest packages for Debian

  The downloader now runs apt-get update before fetching packages on Debian and Ubuntu systems

  References: TPA-575.

- Disable transaction streaming when camo is enabled

  Set `bdr.default_streaming_mode` to `off` when `--enable_camo` is given

  References: TPA-550.

- Detect selinux and act accordingly on barman servers

  In minimal_setup, populate ansible_facts.ansible_selinux.status as the full setup module would do.

  On a barman server with the backup api enabled, set the httpd_can_network_connect boolean if required.

  Fix the existing code to set selinux context on a barman server.

  References: TPA-491.



## v23.28 (2024-01-23)

### Notable changes

- TPA-648 Refactor deployment of Patroni clusters

  TPA now sets up replicas before handing over control of the cluster to
  Patroni, rather than setting up the primary only and letting patroni
  set up the replicas.

- TPA-309 Introduce harp_manager_user

  If harp_manager_user is defined in config.yml, TPA will create the
  user, belonging to the `bdr_superuser` role, and set HARP manager to
  operate as this user instead of as the postgres superuser.

### Minor changes

- TPA-157 New option postgres_log_file

  This option sets the postgres log file, whether logging through stderr
  or syslog. The default is '/var/log/postgres/postgres.log', the
  previously hard-coded value.

- TPA-601 New hook barman-pre-config

  This hook is invoked after Barman is installed and its user is set up
  but before it is configured. It can be used for installing
  certificate files or other tasks which need the barman user to exist
  but which must be done before Barman is started.

- TPA-641 Support specifying elastic IP address on AWS clusters

  The key `elastic_ip` on an instance in config.yml can be set to an
  elastic IP address that has already been allocated in order to assign
  it to this instance.

### Bugfixes

- Don't try to install repmgr on an efm cluster running postgres > 11.

- Exit successfully from a deployment when the deployment succeeds but
  we issue a warning about using 2ndQuadrant repositories.

- TPA-463, TPA-583 Interpret wildcards correctly on Debian-family
  systems when downloading packages for offline use.

- TPA-576 Use correct package names for repmgr when installing from PGDG
  repositories.

- TPA-593 Fix barman connection failure when using selinux and a custom
  barman home directory.

- TPA-638 Use correct cluster name in show-password and store-password
  commands when it is different from the directory name.

- TPA-642 Error out cleanly if unavailable 2ndQuadrant repository keys
  are required.

- TPA-644 Sanitise hostnames correctly when the
  --cluster-prefixed-hostnames option is used.

- TPA-656 Ensure packages are correctly copied to the remote host when
  upgrading a cluster using a local repo.

- Misc. documentation changes

## v23.27 (2023-12-19)

### Notable changes

- TPA-553 TPA support for v16 supported software

  Because v23.23 introduced the initial support for installing Postgres v16,
  this change makes sure that TPA correctly handles v16 supported software.

- TPA-562 TPA requires Python v3.9 to work

- TPA-582 Remove dependency on 2q repositories

  Newly configured clusters will now never use 2q repositories.

  The new `--replace-2q-repositories` argument to `tpaexec reconfigure`
  will remove 2q repositories from an existing config.yml and add
  suitable EDB repositories for the cluster's postgres flavour and BDR
  version, if applicable. `tpaexec deploy` will then apply these changes
  to the servers in the cluster.

- TPA-637 Allow a different Barman user when connecting to servers

### Minor changes

- TPA-467 Change octal integers to strings to abide by Ansible risky-octal linting

- TPA-609 No longer rely on Makefile to install tpaexec from source

- TPA-616 Allow deployment regardless of where dependencies originated

- TPA-618 Generate a primary_slot_name on primary for efm

  Generate a primary_slot_name also on primary node to be used in case of
  switchover, to ensure the switched primary will have a physical slot on
  the new primary.

- TPA-626 Improve CAMO commit_scope generation during reconfigure

  Ensure that commit_scope for CAMO enabled partners is generated using
  existing config options from older BDR versions when running tpaexec
  reconfigure command to prepare for major PGD upgrade. Improve default
  value when no previous config exist.

- TPA-631 Warn if existing cluster are stil using 2q repos

- TPA-634 and TPA 483 Support Oracle Linux 7, 8 and 9 on Docker platform

  Support for AWS platform is underway.

## Bugfixes

- TPA-560 Fix some patroni warnings

- TPA-629 Avoid OOM condition by reducing maintenance_work_mem by default

## v23.26 (2023-11-30)

### Minor changes

- Add --cluster-prefixed-hostnames option to `tpaexec configure`

  This makes it easy to avoid hostname clashes on machines hosting more
  than one docker cluster.

- TPA-617 Add packages to enable Docker builds on Mac OS X

- TPA-483 Support Oracle Linux 9 on the Docker platform

- TPA-608 Fix pemserver agent registration

  When there are multiple PEM servers in a cluster, ensure that the
  agent running on a server registers to its local server.

- TPA-628 Improve default CAMO settings for PGD 5

  Set timeout to 60s and require_write_lead to true.


### Bugfixes

- TPA-592 Use bdr_node_name in harp fencing/unfencing

  If bdr_node_name is different from the hostname, use it explicitly
  when fencing or unfencing a HARP node.

- TPA-558 Suppress automatic provision for some deploy options

  When options that will suppress the actual deployment run are given to
 `tpaexec deploy`, don't automatically run provision beforehand.

- TPA-614 Fix BDR 3 to PGD 5 upgrades for CAMO clusters

  When upgrading a BDR 3 cluster which uses CAMO to PGD 5, ensure that
  CAMO config is set up correctly.

- Misc. documentation changes


## v23.25 (2023-11-14)

### Notable changes

- TPA-445 Support upgrades from BDR 3.7 to PGD5

  A BDR 3.7 cluster created with BDR-Always-ON architecture, can now be
  upgraded to the PGD-Always-ON architecture, running PGD5, by using
  `tpaexec reconfigure` to generate a revised config.yml for PGD5 and then
  `tpaexec upgrade` to perform the upgrade.

  Minimum version for PGD5 to upgrade to needs to be 5.3.

  Please refer to the section `Upgrading from BDR-Always-ON to
  PGD-Always-ON` in `tpaexec-upgrade.md` in the documentation for details
  on the upgrade procedure.

  Note: The upgrade procedure for camo enabled clusters is not yet
  supported. This support will come in a later release.

### Minor changes

- TPA-552 Backport upgrade improvements to BDR-Always-ON

  A number of improvements were introduced to the upgrade process for BDR4
  to PGD5 upgrade as part of TPA-387 including improved checks for
  compatibility, simplified handling of components being upgraded, and
  using HARP fencing functionality to guard against writes being directed
  to nodes while they're being upgraded. This change backports some of
  those improvements to BDR-Always-ON upgrades also.

- TPA-603 Support installing PEM on SLES

- TPA-615 Set explicit permissions when creating filesystem objects

  Also partially covers TPA-467. More improvements in this area targeted
  for later versions.

- TPA-462 Add pgd-cli config symlink for pgd-cli v1

  Adds a symlink to the pgd-cli config file for v1 so it could be run
  without having to specify the path via `-f` switch.

- TPA-587 Set node kinds as part of BDR4 deployment and upgrade

  BDR 4.3.0 had introduced support for `alter_node_kind` to set nodes
  kinds as appropriate. This change ensures node kinds are correctly set
  for BDR-Always-ON clusters using BDR version 4.3 and above.

- TPA-604 Switch to using SP5 for SLES 15

  Default cluster configuration from now on will use SP5 when SLES 15 is
  requested.

- Misc. documentation changes

### Bugfixes

- TPA-611 Fix `tpaexec setup` problems for tpaexec-deps users

  v23.24 switched the default ansible installed as part of `tpaexec setup`
  command from 2q-ansible to community ansible which resulted in a
  checksum failure during `tpaexec setup` command for tpaexec-deps users.

- TPA-613 Make sure `pem_server_group` (if specified) applies to pemworker

- TPA-595 Make sure `sar` runs on all nodes

  sys/sysstat role in previous versions installed and configured `sar` but
  it would only set up the cron job responsible for sar on the barman node
  which meant `sar` won't run on other instances. Also instead of cronjob,
  use `systemd` timers for configuring sysstat.

- TPA-605 Remove references to defunct "shared" platform

## v23.24 (2023-10-17)

### Notable changes

- TPA-499 Change default ansible version to community ansible

  `tpaexec setup` now defaults to using community ansible rather than
  2ndQuadrant ansible. The option `--use-2q-ansible` can be used to
  force the use of 2ndQuadrant ansible, which is now deprecated and will
  be removed in a future release. If you are using `--skip-tags`, see
  [the install documentation](docs/src/INSTALL.md).

### Minor changes

- TPA-529 Remove unwanted EDB repositories

  When a repository has been removed from `edb_repositories` in config.yml,
  `tpaexec deploy` now removes it from the nodes.

- TPA-554 Fix harp configuration when proxy and manager are cohosted

  Detect when harp-proxy and harp-manager are running on the same node
  and use a different config file for harp-proxy.

- TPA-472 Update repositories as part of upgrade process

### Bugfixes

- TPA-532 Respect postgres_wal_dir in pg_basebackup invocation

- TPA-578 Accept repmgr as failover manager for subscriber-only nodes in
  BDR clusters

- TPA-594 Fix typo preventing build of ubuntu 22.04 docker images

- TPA-602 Reject the unsupported combination of the BDR-Always-ON
  architecture, the EDB Postgres Extended flavour, and PEM at
  configure-time.

## v23.23 (2023-09-21)

### Notable changes

- TPA-551 Add support for Postgres 16

  Accept `--postgres-version 16` as a valid tpa configure option.
  PG 16 support available for M1 for now. Support for PGD clusters awaits the release of EPAS and PGE version 16 (scheduled for later).
  Also, stop configuring legacy `dl/default/release` 2Q repository by default for it is no longer available for PG versions 16 and above.
  Since PG has removed `postmaster` symlink, make the change where relevant to use `postgres` binary instead.

### Minor changes

- TPA-534, TPA-535 Add SUSE entries for etcd and patroni package lists

- TPA-548 Adjust EFM dependency lists to use JDK 11 by default, except on
  platforms where it is not available (Debian 9 and Ubuntu 18.04)

- TPA-545 Don't exclude PGDG packages if no EDB repositories are in use

  When using EDB repositories, we exclude barman-related packages and
  psycopg2 packages from the PGDG repositories; if no EBD repositories
  are in use, we now don't exclude these packages.

### Bugfixes

- TPA-440 Ensure apache service is enabled and started for PEM

- TPA-471 Run pg-backup-api tests with correct permissions

- TPA-569 Ensure apache service is enabled and started for pg-backup-api

- TPA-527 Fix bdr.standby_slot_names and bdr.standby_slots_min_confirmed checks
  to use correct schema on bdr3 clusters

- TPA-564 Flatten configuration keys for extensions in postgres config

  Instead of supplying configuration keys for extensions as a nested
  dictionary, which doesn't work, we format them as

    extension_name.config_key: "value"

  and put them in a single flat list.

- TPA-536 Construct docker image names correctly

  A locally built docker base image has no digest, so we refer to it by
  its tag when building the final image.

## v23.22 (2023-09-05)

### Notable changes

- TPA-478 Use edb_repositories for M1 by default

  TPA now generates a default configuration for new M1 clusters to use
  the EDB repos 2.0. Access requires a subscription. For details, see
  https://www.enterprisedb.com/repos-downloads

  To use these new repos, you must obtain a subscription token from the
  URL above and "export EDB_SUBSCRIPTION_TOKEN=<your token>" before you
  run "tpaexec deploy".

  Existing clusters are unaffected by this change, regardless of their
  repository configuration.

  You can always override the default repository configuration by using
  `--edb-repositories standard` (or enterprise, depending on which repo
  your subscription provides access to).

  To avoid confusion, TPA does not permit EDB repos 2.0 to be configured
  with the old 2ndQuadrant repos on the same instance. You can specify a
  list of `--2Q-repositories` to use instead, but only if you do not
  specify any `--edb-repositories`.

  (PGD-Always-ON and BDR-Always-ON clusters are unaffected; the former
  will always use EDB repos 2.0, while the latter uses the 2ndQuadrant
  repos, together with EDB repos 1.0 for EPAS.)

### Minor changes

- TPA-526 Make --failover-manager a mandatory configure option for M1

  You must now choose between efm, patroni, and repmgr when generating a
  new cluster configuration. Note that repmgr is not supported for use
  with EPAS clusters.

- TPA-490 Add bash-completion support for pgd-cli with PGD5

### Bugfixes

- TPA-523 Allow creating a replica of a [bdr,subscriber-only] node

  The earlier code incorrectly required 'subscriber-only' to be set on
  the replica, instead of the upstream instance.

- TPA-156 Skip some inapplicable tasks while running in containers

  TPA would skip certain tasks when it knew that the target instances
  were containers, but it would not do so if you deployed to containers
  with `platform: bare` set. Now it uses systemd-detect-virt to decide
  whether to skip those tasks (like setting the hostname or sysctls).

- TPA-444 Ensure consistent permissions for /etc/edb

  Earlier, if you added the pgd-proxy role to a data node in a deployed
  PGD5 cluster, pgd-proxy would fail to start because it did not have
  permissions to open pgd-proxy-config.yml.

- TPA-447 Ensure consistent permissions for /var/log/postgres

  Earlier, the directory could end up with the inappropriate mode 0600
  if a strict umask was set.

- TPA-549 Fix problem with Barman registration for pemagent

  Earlier, repeating `tpaexec deploy` on a Barman instance correctly
  registered with PEM would lose the Barman configuration.

## v23.20 (2023-08-01)

### Notable changes

- TPA-387 Allow upgrades from BDR4 to PGD5

  A cluster created with the BDR-Always-ON architecture, running BDR4,
  can now be upgraded to the PGD-Always-ON architecture, running PGD5,
  by running the new command `tpexec reconfigure` to generate a revised
  config.yml and then `tpaexec upgrade`, which replaces `tpaexec
  update-postgres`, to perform the upgrade.

  The minimum version requirement to start the upgrade is BDR4.3. A
  cluster running an older version of BDR must be upgraded to BDR4.3
  before doing the major-version upgrade.

  Please refer to the section `Upgrading from BDR-Always-ON to
  PGD-Always-ON` in `tpaexec-upgrade.md` in the documentation for
  details on the upgrade procedure.

### Minor changes

- TPA-322 Add source validation

  The new subcommand `tpaexec info validate` runs a checksum over the TPA
  installation and confirms that it matches the one distributed with the
  package. This is not a security mechanism, but rather a way of
  confirming that an installation has not been altered when debugging
  unexpected behaviour.

- TPA-513 Work around broken OpenJDK dependencies on RHEL

  On RHEL8 or RHEL9, when installing EFM, we install OpenJDK as a
  prerequisite, which has a broken dependency on the tzdata-java
  package. So we add tzdata-java explicitly to our package list.

- Bump PyYAML version from 6.0 to 6.0.1

- Update to the latest Debian AMIs for AWS clusters

- Run `tpaexec provision` automatically as part of `tpaexec deploy` or
  `tpaexec upgrade` if config.yml has changed

### Bugfixes

- TPA-521 Use correct user when running pgd-cli on pgd-proxy nodes

  When upgrading a PGD-Always-ON cluster with a pgd-proxy node which is
  not also a BDR node, we now run pgd-cli as a user which is guaranteed
  to exist.

- If the cluster directory has been set up as a git repository, commit
  changes made by `tpaexec relink` correctly

## v23.19 (2023-07-23)

### Notable changes

- TPA-455 Allow physical standby HA for 'subscriber-only' nodes

  'subscriber-only' nodes in a PGD cluster only receive data, which
  makes them a good choice as CDC sources in PGD clusters.  This change
  allows creating physical replicas of subscriber-only nodes, so that
  a replica with the same LSNs is available in case of a failure of a
  subscriber-only node used as a CDC source.

- TPA-453 Accept `--enable-harp-probes` and `--enable-pgd-probes`
  configure options to enable http(s) health probes for harp-proxy and
  pgd-proxy respectively

  These configure options introduce `harp_http_options` and
  `pgd_http_options` settings respectively in the config.yml with minimal
  default options for health probes. See harp.md and pgd-proxy.md
  for details on configuring these options in TPA. For further details on
  health probes usage, consult product documentation for HARP and PGD
  Proxy.

- TPA-392 Introduce initial support for Patroni for M1 clusters

  Accept `--enable-patroni` configure option to enable patroni as the
  failover manager for M1 clusters.  Alternatively, set `failover_manager:
  patroni` in config.yml to enable Patroni support. The initial support is
  for experimental purposes and not recommended for production deployment
  yet. For more details of Patroni support in TPA, refer to patroni.md.

### Minor changes

- TPA-410 Select correct debug package suffix on Debian-like systems

  On Debian-like systems, fix the package selection code so we use `-dbg`
  rather than `-dbgsym` for certain packages where applicable. Previously,
  we always looked for `-dbgsym` packages when installing EPAS, but now
  the same logic applies to EPAS as for other flavours.

- TPA-451 Restrict the character limit for the name of the downloader
  Docker container to a maximum of 64 characters

  When using `tpaexec download-packages` command, the host name for the
  downloader container is formed by adding `-downloader` to the cluster
  name; in the case of a systematically generated cluster name, this can
  result in a name longer than Docker's maximum 64-character limit and
  somewhat confusing error. TPA now simply truncates the name to 64
  characters if necessary when setting the details for the downloader.

- TPA-465 Don't allow hyphens in primary_slot_name

  Our default_primary_slot_name gets set to the inventory_hostname which
  could be using hyphens but Postgres does not accept that and it would
  result in a warning similar to:

      WARNING:  replication slot name \"tpa_amva-mnl-feather\" contains
      invalid character
      HINT:  Replication slot names may only contain lower case letters,
      numbers, and the underscore character.

- TPA-489 Allow version setting for edb-pgd-proxy and edb-bdr-utilities.

  This allows installing specific versions of the named packages instead
  of always installing the latest version.

- TPA-481 Bump default EFM version to 4.7

- TPA-479 Misc. code tidying related changes

- Misc. documentation improvements

### Bugfixes

- TPA-457 Fix regression in PGD 3.7 to 4 upgrades. This was a recent
  regression in 23.18

- TPA-452 Don't use underscore in CN for PEM agent's SSL certificate

  Per RFC 952, hostnames and subsequent CNs can only contain letters,
  digits and hyphens. Some platforms are more tolerant to the violation of
  this rule, on others it results in a error similar to:

      "msg": "Error while creating CSR: The label pemagent_ghzedlcmbnedb01 is not a valid A-label\nThis is probably caused because the Common Name is used as a SAN. Specifying use_common_name_for_san=false might fix this."}

- TPA-456 Fix wrong etcd service name for Debian platforms. This was a
  recent regression affecting Debian-like platforms and resulting in an
  error similar to:

    TASK [etcd/start : Ensure the service state could be found]
    fatal: [kinfolk]: FAILED! => {
        "assertion": false,
        "changed": false,
        "evaluated_to": false,
        "msg": "The systemd service for etcd could not be found"
     }

- TPA-464 Fix problems with installing PGDG etcd packages on RHEL 8

  TPA recently introduced support for installing etcd packages that are
  not specific to PGD installation; mainly for the patroni support in M1
  clusters, but that failed for RHEL 8 because it needs
  pgdg-rhel<ver>-extra repo for etcd package.

- TPA-358 Fix "Failed to commit files to git: b''" during configure

  TPA-238 introduced support for initialising cluster directory as a git
  repository and above error was reported in some scenarios when running
  `tpaexec configure` command. There was an an earlier attempt to fix
  the same problem in 23.17; but apparently it still appeared in some
  cases.

- TPA-403 Respect `generate_password: false` setting for postgres_users
  when generating passwords. Without the fix, TPA would generate and
  overwrite the user password

- Fix volume map creation on aws to take account of region. In v23.18,
  aws clusters in regions other than eu-west-1 would fail with error
  messages mentioning '/dev/sdf'.


## v23.18 (2023-05-23)

### Notable changes

- TPA-316 Support replica setup using pg_basebackup instead of repmgr

  TPA now uses pg_basebackup for initial replica creation instead of
  repmgr, except for postgresql versions before 12.

- TPA-101 Support deploying to SLES 15

  Pass `--os SLES` to `tpaexec configure` to deploy to SLES.

  The M1 and PGD-Always-ON architectures are supported on all platforms.

  Creation of local repositories (and therefore air-gapped installation)
  is not yet supported on SLES

### Minor changes

- TPA-412 Support deploying to RHEL 9

- TPA-418 Minor version upgrade support for PGD 5

- TPA-425 Improve tests run as part of `tpaexec test`

- TPA-101 Build packages to run TPA on SLES 15

- Various documentation updates

### Bugfixes

- TPA-439 Don't try to use 2q repositories on unsupported distributions

- TPA-443 Install server packages for pg_receivewal on older epas

  On barman servers, we need to install the postgresql server package
  for certain flavour/version/os combinations so that the pg_receivewal
  binary will be present. This fixes the logic to include the case of
  epas version < 13.

- TPA-448 Fix device lookup failures on AWS

  This fixes intermittent failures to create symlinks to block devices
  on AWS hosts, which manifested as successful provision followed by
  failing deployment.

## v23.17 (2023-05-10)

### Notable changes

- TPA-383 Require --pgd-proxy-routing global|local to be specified at
  configure time for PGD-Always-ON clusters

  This option determines how PGD-Proxy instances will route connections
  to a write leader. Local routing will make every PGD-Proxy route to
  a write leader within its own location (suitable for geo-sharding
  applications). Global routing will make every proxy route to a
  single write leader, elected amongst all available data nodes across
  all locations (i.e., all pgd-proxy instances will be attached to the
  top-level node group).

  (This option entirely replaces the earlier --active-locations option,
  and also resolves some problems with the earlier top-level routing
  configuration.)

- TPA-102 Support deploying to Ubuntu 22.04

  TPA can now provision and deploy nodes running Ubuntu 22.04 ("Jammy
  Jellyfish") on either docker containers or AWS.

### Minor changes

- Update AWS AMIs for RHEL7 and RHEL8

- Documentation improvements

### Bugfixes

- TPA-404 Don't remove groups from an existing postgres user

- Fix `Failed to commit files to git: b''` error from `tpaexec configure`;
  if the commit fails, the correct error message will now be shown

- TPA-416 Correctly sanitise subgroup names

  If subgroup names contain upper-case letters, lowercase them rather
  than replacing them with underscores.

- TPA-415 Ensure Postgres is correctly restarted, if required, after
  CAMO configuration

- TPA-400 Ensure etcd config changes are idempotent

  Enforce an ordering on the list of etc nodes and create data files
  with correct permissions, so that etcd doesn't get restarted
  unnecessarily on second and subsequent deployments.

## v23.16 (2023-03-21)

### Notable changes

- TPA-372 Use a single location by default for PGD-Always-ON clusters

  The default PGD-Always-ON cluster will now have one location with an
  associated subgroup containing 2 data nodes and 1 witness node.

- TPA-370 Run pgd-proxy on data nodes by default

  Adopt the old `--cohost-proxies` behaviour by running pgd-proxy
  on data nodes by default.

  Add a new option: `--add-proxy-nodes-per-location N` which will create
  separate proxy instances.

- TPA-371 Add a witness node automatically if `--data_nodes_per_location`
  is even and print a warning if you specify a cluster with only two
  locations

  Rename `--add-witness-only-location` back to `--witness-only-location`
  because we're NOT adding a location, but merely designating an already-named
  (in `--location-names`) location as a witness-only one.

### Minor changes

- TPA-368 Require both Postgres flavour and version to be specified explicitly
  at `tpaexec configure` time

  Here are some examples:

  * --postgresql 14
  * --edbpge 15
  * --epas 15 --redwood
  * --postgresql --postgres-version 14

- TPA-385 Improve both documentation and code around the use of the various
  different supported EDB software repositories

- TPA-374 Don't include PGDG repository by default for PGD-Always-ON clusters

### Bugfixes

- TPA-318 Use EFM by default to manage failover with EPAS

- TPA-378 Do not install pglogical for M1 architecture by default

## v23.15 (2023-03-15)

### Minor changes

- Update includes changes to dependency mappings

## v23.14 (2023-02-24)

### Bugfixes

- TPA-365 Don't set edb_repositories for non-PGD5 clusters

### Minor changes

- TPA-360 Use multi-line BDR DCS configuration in HARP's config.yml

## v23.13 (2023-02-23)

### Bugfixes

- TPA-362 Don't enable old EDB repo with PGD-Always-ON and `--epas`

- TPA-363 Fix error with PGD-Always-ON and `--postgres-version 15`

## v23.12 (2023-02-21)

### Notable changes

- TPA-180, TPA-342 Introduce full support for PGD5, including CAMO
  configuration support based on commit scopes

- Introduce support for EDB Postgres Extended repository and packages

### Minor changes

- TPA-270 Preliminary support for configuring multi-region AWS clusters

  Multi-region clusters require manual setup of VPCs and VPC peering, and
  editing config.yml to ensure subnets do not overlap.

- Enable proxy routing (and, therefore, subgroup RAFT) automatically for
  --active-locations, and remove the configure option to enable subgroup
  RAFT globally

### Bugfixes

- TPA-327 Ensure the EDB_SUBSCRIPTION_TOKEN is not logged

- TPA-303 Allow the user to suppress addition of the
  products/default/release repo to tpa_2q_repositories

- TPA-359 Ensure that nodes subscribe to bdr_child_group, if available

  In clusters with multiple subgroups, TPA did not expect instances to
  be subscribed to the replication sets for both the top group and the
  subgroup, so it would incorrectly remove the latter from the node's
  subscribed replication sets.

- TPA-354 Fail reliably with a useful error if Postgres doesn't start

  Due to an Ansible bug, the deployment would not fail if Postgres did
  not start on some instances, but did start on others (e.g., due to a
  difference in the configuration). Continuing on with the deployment
  resulted in errors when trying to access `cluster_facts` for the
  failed hosts later.

- Don't call bdr.alter_node_replication_sets() on witnesses for BDR 4.3+

  This adjusts to a new restriction in BDR versions where witness nodes
  are not handled with a custom replication set configuration.

- TPA-174, TPA-248 Replace harcoded "barman" references to enable use
  of the barman_{user,group} settings to customise the barman user and
  home directory

- TPA-347 Add shared_preload_libraries entries, where appropriate, for
  extensions mentioned under postgres_databases[*].extensions

- TPA-198 Ensure that pgaudit does not appear before bdr in
  shared_preload_libraries (to avoid a known crash)

- Fix syntax error (DSN quoting) in pgd-cli config file

- Sort endpoints in pgd-proxy config to avoid file rewrites

  This will likely require a pgd-proxy restart on the next deploy (but
  it will avoid unnecessary future rewrites/restarts on subsequent
  deploys).

- Fix an error while installing rsync from a local-repo on RH systems

- Fix an error with Apache WSGI module configuration for PEM 9 on Debian
  systems

- Don't remove the bdr extension if it has been created on purpose, even
  if it is unused.

## v23.11 (2023-01-31)

### Notable changes

- TPA-180 Introduce experimental support for PGD-Always-ON architecture (to be
  released later this year).

  PGD-Always-ON architecture will use the upcoming BDR version 5.
  Initial support has been added for internal purposes and will be improved in
  upcoming releases.

### Minor changes

- TPA-349 Bump dependency versions

  Bump cryptography version from 38.0.4 to 39.0.0

  Bump jq version from 1.3.0 to 1.4.0

- TPA-345 Change TPAexec references to TPA in documentation.

  Update the documentation to use 'TPA' instead of 'TPAexec' when referring
  to the product.

## v23.10 (2023-01-04)

### Minor changes

- TPA-161 Introduce `harp_manager_restart_on_failure` setting (defaults
  to false) to enable process restart on failure for the harp-manager
  systemd service

### Bugfixes

- TPA-281 Delete FMS security groups when deprovisioning an AWS cluster

  Fixes a failure to deprovision a cluster's VPC because of unremoved
  dependencies.

- TPA-305 Add enterprisedb_password to pre-generated secrets for Tower

- TPA-306 Prefer PEM_PYTHON_EXECUTABLE, if present, to /usr/bin/python3

  Fixes a Python module import error during deployment with PEM 9.0.

- TPA-219 Make pem-agent monitor the bdr_database by default on BDR
  instances

## v23.9 (2022-12-12)

### Bugfixes

- TPA-301 Fix auto-detection of cluster_dir for Tower clusters

  When setting cluster_dir based on the Tower project directory, we now
  correctly check for the existence of the directory on the controller, and
  not on the instances being deployed to.

- TPA-283 Add dependency on psutil, required for Ansible Tower.

- TPA-278 Remove "umask 0" directive from rsyslog configuration, which
  previously resulted in the creation of world-readable files such as
  rsyslogd.pid .

- TPA-291 Respect the postgres_package_version setting when installing
  the Postgres server package to obtain pg_receivewal on Barman instances.

## v23.8 (2022-11-30)

### Notable changes

- TPA-18 Support Ansible Tower 3.8

  This release supports execution of `deploy.yml` (only) on a `bare` cluster
  (i.e., with existing servers) through Ansible Tower 3.8.

  Install TPAexec on the Tower server and run `tpaexec setup` to create
  a virtual environment which can be used in Tower Templates to run
  TPAexec playbooks.

  Use the `--use-ansible-tower` and `--tower-git-repository` configure
  options to generate a Tower-compatible cluster configuration.

  For details, see [Ansible Tower](tower.md).

### Minor changes

- TPA-238 Initialise the cluster directory as a git repository

  If git is available on the system where you run TPAexec, `tpaexec configure`
  will now initialise a git repository within the cluster directory by default.
  If git is not available, it will continue as before.

  To avoid creating the repository (for example, if you want to store the
  cluster directory within an existing repository), use the `--no-git`
  option.

## v23.7 (2022-11-09)

### Notable changes

- TPA-234 Support the community release of Ansible 2.9

  TPAexec used to require the 2ndQuadrant/ansible fork of Ansible 2.9.
  In this release, you may instead choose to use the community release
  of Ansible with the `tpaexec setup --use-community-ansible`.

  For now, the default continues to be to use 2ndQuadrant/ansible. This
  will change in a future release; support for 2ndQuadrant/ansible will
  be dropped, and Ansible will become the new default.

### Minor changes

- TPA-209 Accept `--postgres-version 15` as a valid `tpaexec configure`
  option, subsequent to the release of Postgres 15

- TPA-226 Accept IP addresses in the `--hostnames-from` file

  Formerly, the file passed to `tpaexec configure` was expected to
  contain one hostname per line. Now it may also contain an optional IP
  address after each hostname. If present, this address will be set as
  the `ip_address` for the corresponding instance in config.yml.

  (If you specify your own `--hostnames-from` file, the hostnames will
  no longer be randomised by default.)

- TPA-231 Add a new bdr-pre-group-join hook

  This hook is executed before each node joins the BDR node group. It
  may be used to change the default replication set configuration that
  TPAexec provides.

- TPA-130 Use the postgresql_user module from community.postgresql

  The updated module from the community.postgresql collection is needed
  in order to correctly report the task status when using a SCRAM
  password (the default module always reports `changed`).

- TPA-250 Upgrade to the latest versions of various Python dependencies

### Bugfixes

- TPA-220 Ensure LD_LIBRARY_PATH in .bashrc does not start with ":"

- TPA-82 Avoid removing BDR-internal ${group_name}_ext replication sets

- TPA-247 Fix "'str object' has no attribute 'node_dsn'" errors on AWS

  The code no longer assigns `hostvars[hostname]` to an intermediate
  variable and expects it to behave like a normal dict later (which
  works only sometimes). This fixes a regression in 23.6 reported for
  AWS clusters with PEM enabled, but also fixes other similar errors
  throughout the codebase.

- TPA-232 Eliminate a race condition in creating a symlink to generated
  secrets in the inventory that resulted in "Error while linking:
  [Errno 17] File exists" errors

- TPA-252 Restore code to make all BDR nodes publish to the witness-only
  replication set

  This code block was inadvertently removed in the v23.6 release as part
  of the refactoring work done for TPA-193.

## v23.6 (2022-09-28)

### Notable changes

- TPA-21 Use boto3 (instead of the unmaintained boto2) AWS client library
  for AWS deployments. This enables SSO login and other useful features.

- TPA-202 Add harp-config hook. This deploy-time hook executes after HARP
  is installed and configured and before it is started on all nodes
  where HARP is installed.

### Bugfixes

- TPA-181 Set default python version to 2 on RHEL 7. Formerly, tpaexec
  could generate a config.yml with the unsupported combination of RHEL 7
  and python 3.

- TPA-210 Fix aws deployments using existing security groups. Such a
  deployment used to fail at provision-time but will now work as
  expected.

- TPA-189 Remove group_vars directory on deprovision. This fixes a
  problem that caused a subsequent provision to fail because of a
  dangling symlink.

- TPA-175 Correctly configure systemd to leave shared memory segments
  alone. This only affects source builds.

- TPA-160 Allow version setting for haproxy and PEM. This fixes a bug
  whereby latest versions of packages would be installed even if a
  specific version was specified.

- TPA-172 Install EFM on the correct set of hosts. EFM should be
  installed only on postgres servers that are members of the cluster,
  not servers which have postgres installed for other reasons, such as
  PEM servers.

- TPA-113 Serialize PEM agent registration. This avoids a race condition
  when several hosts try to run pemworker --register-agent at the same
  time.

## v23.5 (2022-08-22)

### Notable changes

- TPA-81 Publish tpaexec and tpaexec-deps packages for Ubuntu 22.04 Jammy
- TPA-26 Support harp-proxy and harp-manager installation on a single node.
  It is now possible to have both harp-proxy and harp-manager service running
  on the same target node in a cluster.

## v23.4 (2022-08-05)

### Bugfixes

- TPA-152 fix an issue with locale detection during first boot of Debian
  instances in AWS Hosts would fail to complete first boot which would
  manifest as SSH key negotiation issues and errors with disks not found
  during deployment. This issue was introduced in 23.3 and is related to
  TPA-38

## v23.3 (2022-08-03)

### Notable changes

- TPA-118 Exposed two new options in harp-manager configuration. The
  first sets HARP `harp_db_request_timeout` similar to dcs
  request_timeout but for database connections and the second
  `harp_ssl_password_command` specifies a command used to de-obfuscate
  sslpassword used to decrypt the sslkey in SSL enabled database
  connection

### Minor changes

- TPA-117 Add documentation update on the use of wildcards in
  `package_version` options in tpaexec config.yml. This introduces a
  warning that unexpected package upgrades can occur during a `deploy`
  operation. See documentation in `tpaexec-configure.md` for more info
- TPA-38 Add locale files for all versions of Debian, and RHEL 8 and
  above. Some EDB software, such as Barman, has a requirement to set the
  user locale to `en_US.UTF-8`. Some users may wish to also change the
  locale, character set or language to a local region. This change
  ensures that OS files provided by libc are installed on AWS instances
  during firstboot using user-data scripts. The default locale is
  `en_US.UTF-8`. See `platform_aws.md` documentation for more info
- TPA-23 Add log config for syslog for cluster services Barman, HARP,
  repmgr, PgBouncer and EFM. The designated log server will store log
  files received in `/var/log/hosts` directories for these services
- TPA-109 Minor refactoring of the code in pgbench role around choosing
  lock timeout syntax based on a given version of BDR

### Bugfixes

- TPA-147 For clusters that use the source install method some missing
  packages for Debian and Rocky Linux were observed. Debian receives
  library headers for krb5 and lz4. On RedHat derived OSs the mandatory
  packages from the "Development Tools" package group and the libcurl
  headers have been added
- TPA-146 Small fix to the method of package selection for clusters
  installing Postgres 9.6
- TPA-138 Addresses a warning message on clusters that use the "bare"
  platform that enable the local-repo configure options. As the OS is
  not managed by TPAexec in the bare platform we need to inform the user
  to create the local-repo structure. This previously caused an
  unhandled error halting the configure progress
- TPA-135 When using `--use-local-repo-only` with the "docker" platform
  and the Rocky Linux image initial removal of existing yum repository
  configuration on nodes would fail due to the missing commands `find`
  and `xargs`. This change ensures that if the `findutils` package
  exists in the source repo it will be installed first
- TPA-111 Remove a redundant additional argument on the command used to
  register agents with the PEM server when `--enable-pem` option is
  given. Previously, this would have caused no problems as the first
  argument, the one now removed, would be overridden by the second
- TPA-108 Restore SELinux file context for postmaster symlink when
  Postgres is installed from source. Previously, a cluster using a
  SELinux enabled OS that is installing postgres from source would fail
  to restart Postgres as the systemd daemon would be unable to read the
  symlink stored in the Postgres data bin directory. This was discovered
  in tests using a recently adopted Rocky Linux image in AWS that has
  SELinux enabled and in enforcing mode by default

## v23.2 (2022-07-12)

### Notable changes

- Add support for Postgres Backup API for use with Barman and PEM.
  Accessible through the `--enable-pg-backup-api` option.
- SSL certificates can now be created on a per-service basis, for
  example the server certificate for Postgres Backup API proxy service.
  Certificates will be placed in `/etc/tpa/<service>/<hostname>.cert`
  These certificates can also be signed by a CA certificate generated
  for the cluster.
- Placement of Etcd for the BDR-Always-ON architecture
  When using 'harp_consensus_protocol: etcd', explicitly add 'etcd' to
  the role for each of the following instances:
  - BDR Primary ('bdr' role)
  - BDR Logical Standby ('bdr' + 'readonly' roles)
  - only for the Bronze layout: BDR Witness ('bdr' + 'witness' roles)
  - only for the Gold layout: Barman ('barman' role)
  Credit: Gianni Ciolli <gianni.ciolli@enterprisedb.com>

### Minor changes

- Replace configure argument `--2q` with `--pgextended` to reflect
  product branding changes. Existing configuration will retain expected
  behaviour.
- Improve error reporting on Docker platform compatibility checks when
  using version 18 of docker, which comes with Debian old stable.
- Add some missing commands to CLI help documentation.
- Improved error reporting of configure command.
- Add initial support for building BDR 5 from source.
  Credit: Florin Irion <florin.irion@enterprisedb.com>
- Changes to ensure ongoing compatibility for migration from older
  versions of Postgres with EDB products.

### Bugfixes

- Fixed an issue which meant packages for etcd were missing when using
  the download-packages command to populate the local-repo.
- Fixed an issue affecting the use of efm failover manager and the
  selection of its package dependencies

## v23.1 (2022-06-20)

This release requires you to run `tpaexec setup` after upgrading (and
will fail with an error otherwise)

### Changes to package installation behaviour

In earlier versions, running `tpaexec deploy` could potentially upgrade
installed packages, unless an exact version was explicitly specified
(e.g., by setting postgres_package_version). However, this was never a
safe, supported, or recommended way to upgrade. In particular, services
may not have been safely and correctly restarted after a package upgrade
during deploy.

With this release onwards, `tpaexec deploy` will never upgrade installed
packages. The first deploy will install all required packages (either a
specific version, if set, or the latest available), and subsequent runs
will see that the package is installed, and do nothing further. This is
a predictable and safe new default behaviour.

If you need to update components, use `tpaexec update-postgres`. In this
release, the command can update Postgres and Postgres-related packages
such as BDR or pglogical, as well as certain other components, such as
HARP, pgbouncer, and etcd (if applicable to a particular cluster).
Future releases will safely support upgrades of more components.

### Notable changes

- Run "harpctl apply" only if the HARP bootstrap config is changed

  WARNING: This will trigger a single harp service restart on existing
  clusters when you run `tpaexec deploy`, because config.yml is changed
  to ensure that lists are consistently ordered, to avoid unintended
  changes in future deploys

- Add `tpaexec download-packages` command to download all packages
  required by a cluster into a local-repo directory, so that they can be
  copied to cluster instances in airgapped/disconnected environments.
  See air-gapped.md and local-repo.md for details

- Require `--harp-consensus-protocol <etcd|bdr>` configure option
  for new BDR-Always-ON clusters

  TPAexec no longer supplies a default value here because the choice
  of consensus protocol can negatively affect failover performance,
  depending on network latency between data centres/locations, so the
  user is in a better position to select the protocol most suitable for
  a given cluster.

  This affects the configuration of newly-generated clusters, but does
  not affect existing clusters that use the former default of `etcd`
  without setting harp_consensus_protocol explicitly

### Minor changes

- Install openjdk-11 instead of openjdk-8 for EFM on distributions where
  the older version is not available

- Accept `harp_log_level` setting (e.g., under cluster_vars) to override
  the default harp-manager and harp-proxy log level (info)

- Configure harp-proxy to use a single multi-host BDR DCS endpoint DSN
  instead of a list of individual endpoint DSNs, to improve resilience

- Omit extra connection attributes (e.g., ssl*) from the local (Unix
  socket) DSN for the BDR DCS for harp-manager

### Bugfixes

- Ensure that harp-manager and harp-proxy are restarted if their config
  changes

- Fix harp-proxy errors by granting additional (new) permissions
  required by the readonly harp_dcs_user

- Disable BDR4 transaction streaming when CAMO is enabled

  If bdr.enable_camo is set, we must disable bdr.default_streaming_mode,
  which is not compatible with CAMO-protected transactions in BDR4. This
  will cause a server restart on CAMO-enabled BDR4 clusters (which could
  not work with streaming enabled anyway).

## v22.14 (2022-05-16)

### Notable changes

- Add `--enable-local-repo` configure option to ship packages that you
  provide (in cluster_dir/local-repo) to a new local package repository
  on each instance in the cluster

- Add `--use-local-repo-only` option to create a local repo as described
  above and also disable all other repositories on the instance. In this
  case, the local repo must contain all packages required for
  deployment, starting with rsync and Python

- Change the default HARP v2 consensus protocol from etcd to bdr

  This does not affect existing clusters that are using etcd (even if
  they do not have harp_consensus_protocol set explicitly)

- Require Docker CE v20.10+

  There are a number of problems on older versions of Docker that we can
  neither fix, nor work around. We now require the latest major release
  of Docker CE.

- Support running pgbouncer in front of harp-proxy on the same instance
  (by setting `role: [harp-proxy, pgbouncer]` on the instance)

  This allows applications to connect to harp-proxy through pgbouncer,
  and is not the same thing as running harp-proxy in pgbouncer mode,
  which involves harp-proxy connecting to Postgres through pgbouncer.
  (These two modes are mutually exclusive.)

### Minor changes

- Restart harp-proxy one by one on proxy instances

  The earlier behaviour, which was to restart all harp-proxy services
  simultaneously if there was any configuration change, could lead to
  disruption in traffic routing

- Wait for BDR to achieve RAFT consensus before running "harpctl apply"

- Increase the default HARP DCS request timeout to 6s

  Note: this will cause a harp restart on deploy.

- Change the default M1 configuration to not use openvpn

  The functionality is still supported, if you need to use it, but now
  you have to set `vpn_network` and assign an `openvpn-server` instance
  explicitly. Does not affect existing clusters.

- Add `bdr_camo_use_raft_for_local_mode: [true|false]` setting to
  configure the RAFT fallback mode for CAMO pairs in BDR 4.1 (only)

- Install edb-pgd-cli and edb-bdr-utilities packages by default on all
  BDR (4.1 and above only) instances

### Bugfixes

- Check that TPA_2Q_SUBSCRIPTION_TOKEN is set when needed

  Fixes a 403 error during the repository in clusters configured to use
  Postgres Extended (--2q) without setting --2Q-repositories and without
  providing a token.

- Before restarting etcd, check endpoint health of etcd instances in the
  same harp_location only (since instances in other locations may not be
  reachable)

## v22.13 (2022-04-25)

### Notable changes

- Create a long-lived S3 bucket by default for new AWS clusters

  Earlier versions used a hardcoded default S3 bucket, which was not accessible
  outside an internal AWS account, requiring you to always set `cluster_bucket`
  explicitly

  The name of the automatically-created bucket is based on your AWS username,
  and you will be prompted to confirm that you want to create it. It will not
  be removed when you deprovision the cluster (this means the bucket will be
  reused for any clusters you create, which we recommend)

  To use an existing S3 bucket, use the `--cluster-bucket name-of-bucket`
  configure option to set `cluster_bucket: name-of-bucket` in config.yml
  (as before, existing S3 buckets will never be removed)

- Make `--layout` a required parameter for configuring a new BDR-Always-ON
  cluster. Previously it would use `platinum` as default

- Remove support for generating configurations for the BDR-Simple testing
  architecture

  (Existing clusters are unaffected by this change)

- Remove support for the LXD and Vagrant platforms

  (VMs provisioned with Vagrant can still be used as bare instances in TPAexec
  if required; existing Vagrantfiles will also continue to work)

- Introduce alpha support for Postgres Enterprise Manager (PEM)

  (Not recommended for production deployments yet)

### Minor changes

- Set default compaction configuration for etcd keyspace to keep 10 (ten)
  revisions

  Earlier versions did not set default compaction settings. Since etcd keeps
  an exact history of its keyspace, this history should be periodically compacted
  to avoid performance degradation and eventual storage space exhaustion

- Ensure that etcd restart happens on one instance at a time

  (When an etcd cluster is already serving as the consensus layer for HARP,
  we can't afford to restart etcd on all instances simultaneously, because
  that will cause HARP to become unhappy and break routing)

### Bugfixes

- Correctly deprovision any internet gateway created along with a VPC for an
  AWS cluster (earlier, deprovision would fail when trying to remove the VPC)

## v22.12 (2022-04-08)

### Bugfixes

- Correct file copy path during tpaexec setup for dynamic inventory scripts

## v22.11 (2022-04-08)

### Bugfixes

- Use correct Ansible release tarball download location (to fix 404 errors
  while downloading Ansible during `tpaexec setup`)

- Ensure that the bundled ansible from tpaexec-deps is used, if present
  (workaround for a pip limitation)

- Ensure that we install a Postgres-specific logrotate configuration only on
  Postgres instances

## v22.10 (2022-03-31)

### Notable changes

- Improve automated testing

- Introduce vulnerability scanning in CI

### HARP-related changes

- Add support for harp_dcs_client_dsn_attributes setting to pass extra connection
  parameters for harp-proxy's connection to BDR as DCS

- Use `harp_listen_address` as HARP2 listen address to override the default,
  which is to listen on all interfaces

- Fix proxy start error by granting required execute privileges to harp_dcs_user

### Minor changes

- Allow the use of FQDNs for Docker containers

- Ensure that ping is installed on EFM nodes for EFM internal use

- Add `Rocky` to `--os` available option list for AWS clusters

- Use latest AMIs for Ubuntu and Debian on aws platform

- Bump EFM's default version to 4.4

- Miscellaneous documentation improvements

### Bugfixes

- Fix repmgr source builds switching from `git://` to `https://` for repository
  links since github stopped supporting the former

- Fix "module 'jinja2.ext' has no attribute 'with_'" errors from inventory
  script with recent versions of Jinja2

- Update hostname validation to be RFC compliant

## v22.9 (2022-02-24)

### Notable changes

- Deploy harp-proxy with the "builtin" proxy instead of pgbouncer

  This change applies to existing clusters, which will be transparently
  reconfigured to use the new proxy mode when you run `tpaexec deploy`.

  Future versions of harp will no longer support embedded pgbouncer, but for now,
  you can set `harp_proxy_mode: pgbouncer` explicitly to keep using it.

- Create a new harp-postgres.target that stops/starts both Postgres and
  harp-manager together (i.e., `systemctl restart harp-postgres.target`
  will correctly stop harp-manager, restart postgres, and then start
  harp-manager)

### Minor changes

- Remove "pwgen" as a dependency for the tpaexec package

- Add archive-logs command to fetch logs from cluster instances

### Bugfixes

- Set `postgres_port` correctly when granting permissions to the
  harp_dcs_user

- Use the correct Unix socket path to connect to EPAS even when using
  a non-EPAS libpq or vice versa

- Fix a problem with adding new BDR instances in a different node group,
  which would cause the "Override first_bdr_primary if required" task to
  fail with an "undefined variable" error

- Fix conninfo generation to not duplicate dbname/user parameters (a
  cosmetic problem, but potentially confusing)

- Fix an error about `private_ip` not being defined when generating
  efm.properties

- Generate harp configuration only on instances where we install harp

- Ensure that backups taken during the initial deploy are fully
  consistent by using `barman backup --wait`

## v22.8 (2022-02-08)

### Major changes

- Upgrade ansible to v2.9

### New Features

- Added support for the Alma Linux distribution

### Minor Changes

- Modify systemd service files for postgres on Harp enabled hosts that
  require alternative user accounts.
  Always run Harp services as the same user as Postgres, regardless of
  the flavour in use.

### Bugfixes

- Fix a problem that caused the ec2 inventory to return "none" instead of a
  private IP address for EC2 instances with `assign_public_ip: no`;
  note that you must also have `ec2_instance_reachability: private`
  set for such clusters

- Fix OS detection for Rocky Linux when used on non-docker platforms. This
  previously affected the host name change during deployment.
  We now enforce the use of systemd to change host names.

## v22.7 (2022-02-07)

- Unpublished version

## v22.6 (2022-01-31)

### Major changes

- Change the default image on Docker and Vagrant to rockylinux:8 (since
  centos:8 is now EOL). Please remove your existing tpa/redhat images to
  rebuild using the new base image

### Minor changes

- Allow harp-proxy to use a separate `harp_dcs_user` to connect to BDR
  when using `harp_consensus_protocol: bdr`

### Bugfixes

- Fix an "nodename is tagged as witness for nodename, but is registered
  as a primary already" error from repmgr on BDR witness instances

- Install and start harp only on primary candidates and proxy instances,
  and exclude subscriber-only nodes from the DCS endpoint list

## v22.5 (2022-01-27)

### Minor changes

- Run HARP v2 as `enterprisedb` user when deployed with EPAS

- Per instance use of `listen_address` and `listen_port` in HARP v2
  to cater to multi-proxy setup

### Bugfixes

- Default values for `request_timeout` and `watch_poll_interval`
  in HARP v2 config should not use quotes

- Default to products/bdr_enterprise_3_7/release repository when
  `postgresql_flavour` is '2q' for BDR architectures.

## v22.4 (2022-01-21)

### Bugfixes

- Fixed a harp config defect where listen_address is not always set
  to the proxy hostname.

## v22.3 (2022-01-20)

### Minor changes

- Moved listen_addr and listen_port in harp2 configuration files

- Add hook to prevent removal of pgbouncer user from database

### Bugfixes

- Rsyslog log-server not sending/storing postgres logs as intended

## v22.2 (2022-01-19)

### Minor changes

- Ensure correct package name for repmgr on RedHat from BDR Enterprise
  2q repositories is used. This caters for a fairly small corner case
  therefore previously configured clusters where this is seen should
  be refreshed manually if a package conflict is seen. This can be done
  by removing any packages matching "*repmgr*" before rerunning deploy.

## v22.1 (2022-01-19)

### Minor changes

- Revise max_worker_processes and set a reasonable floor value
  of 16. Normally this value is calculated using the number of
  postgres instances as a base value, the new base default is now
  used if this results in a lower value than the floor.

- Update Training architecture to current conventions

- Make global lock timeouts configurable for pgbench init

- Expose additional config for harp template files, so they can
  be customised by the user

### Bugfixes

- Ensure permissions for rsyslog managed postgres log is correct. On
  existing clusters built with Ubuntu OS rsyslog is set to drop root
  privileges after start up. This makes it impossible for log files
  to be owned by another user. In TPAexec postgres log files are owned
  by the user `postgres`. This change will ensure existing log files are
  owned by this user as well as disabling the privilege drop configuration
  in rsyslog.

- Fix case where zero postgres instances exist. If no instances in a
  cluster have a role which would mean postgres wouldn't be installed
  a "deploy" action will complete successfully. This was not the case
  previously.

## v21.11 (2021-12-23)

### Minor changes

- Install HARP v2 packages from the products/harp/release repository (so
  that it no longer a separate EDB_REPO_CREDENTIALS_FILE to install)

- Install the latest available haproxy version by default (set
  haproxy_package_version explicitly to override)

- Use harp-proxy instances instead of haproxy instances in the default
  BDR-Always-ON configuration; existing configurations are unaffected

- Increase default EFM version to v4.2

### Bugfixes

- Set max_worker_processes to a minimum of 16 (fixes an error that
  caused EPAS to not start with the default dbms_aq.max_workers)

## v21.10 (2021-12-15)

### Minor changes

- Update the names of harp-related packages (now available in the EDB
  repository, i.e., {apt,yum}.enterprisedb.com)

- Use the new `pgdgNN-debuginfo` repositories (fixes errors with missing
  debuginfo packages for Postgres)

- Use HARP as default failover manager for BDR-Always-ON architecture

- Documentation improvements, notably for BDR Always-ON and Barman

## v21.9 (2021-12-01)

- Fix incorrect default value for `enable_camo`

## v21.8 (2021-11-30)

### New features

- Add new bronze/silver/gold/platinum layouts for BDR-Always-ON,
  selectable using the `--layout gold` configure option

- Add experimental HARP v2 support with any BDR-Always-ON layout

- Add declarative configuration for BDR witnesses (just set the
  instance's role to bdr+witness)

### Minor changes

- Avoid repeated expensive invocations of semanage/restorecon for custom
  Postgres directory locations (e.g., tablespaces)

- Support newly-published repmgr packages for EPAS; this means you no
  longer have to deploy with `repmgr_installation_method: src`

- Allow setting `barman_archiver: on` for an instance to enable WAL
  archiving to Barman with a suitable default `archive_command`

- Support deployment of BDR v4 (still experimental), including
  on-the-fly (symmetric) CAMO configuration changes

- Allow `enable_camo` to be set (earlier, it was always "on" by default
  if CAMO was enabled)

### Bugfixes

- Fix handling of the default value of shared_preload_libraries on EPAS
  installations

- Fix some minor breakage related to the change in the location of the
  documentation, notably `tpaexec info architectures` and `tpaexec info
  platforms`

- Fix a provision-time error from `find_replica_tablespace_mismatches`
  for Docker instances with user-defined `volumes` entries

- Fix the `--enable-camo` option to correctly generate CAMO partner
  annotations on BDR instances

- Fix rsyslog configuration to set logfile ownership to root/root (and
  not the postgres user, which may not exist on the log server)

- Don't set `operator_precedence_warning` for Postgres v14+

## v21.7 (2021-09-20)

### New features

- Accept optional `postgres_wal_dir` setting to determine location of
  pg_wal during initial deployment; if there is a volume marked with
  `volume_for: postgres_wal`, it will be used by default.

- Support declarative configuration of `postgres_tablespaces`; also, any
  volumes marked with `volume_for: postgres_tablespace` will be used to
  set up tablespaces by default.

- Support declarative configuration of BDR subscriber-only groups: any
  BDR instance with 'subscriber-only' in its role will join a default
  cluster-wide subscriber-only node group (but more complex topologies
  are possible by explicitly setting `bdr_child_group` to point to any
  subscriber-only node group declared in `bdr_node_groups`).

### Minor changes

- Install Postgres v13 and BDR v3.7 by default on new clusters

- Add preliminary support for Oracle Linux 7 and 8 by treating it
  exactly the same as RHEL 7 or 8

- Update EC2 AMIs to the latest available versions

### Bugfixes

- Fix errors like "Repository 'epel' is missing name in configuration"
  by ensuring we only edit existing files to add `exclude` entries, and
  not create empty .repo and other YUM-related configuration files

- Fix error about upstream_primary being undefined during template
  expansion of efm.properties on EFM witnesses

- Fix "Unrecognised host=x in primary_conninfo" error during deployment
  after running `efm promote` (by accepting and translating IP addresses
  in addition to hostnames)

- Fail early if you run `tpaexec deploy` without running `tpaexec
  provision` first

- Fail with a sensible error message if Python installation fails

## v21.6 (2021-08-09)

### Minor changes

- Minor documentation improvements

### Bugfixes

- Delay granting roles to users until after extensions are created so
  all the dependencies for role assignments are met. This was a recent
  regression.

## v21.5 (2021-07-26)

### Minor changes

- Allow Postgres 13 and BDR3 as a supported combination

### Bugfixes

- Correctly create the bdr extension in the default 'edb' database on EPAS

- Set up /etc/hosts to use openvpn IPs for cluster instances when openvpn
  is used in the cluster. This used to work correctly, but was a recent
  regression.

## v21.4 (2021-07-09)

### Minor changes

- Remove bdr extension from databases other than bdr_database where it
  is unused (it used to be created in template1 and inherited by other
  databases earlier, but the BDR developers advised against this)

- Allow `postgres_databases` to specify extensions and languages to
  create within a single database (and this mechanism is now used to
  create the bdr extension only in bdr_database)

- Improve installation instructions

### Bugfixes

- Install tmux instead of the deprecated screen on RHEL8 (though the
  screen package is available in EPEL, as before)

## v21.3 (2021-06-21)

### Minor changes

- Improve pgbouncer and HAProxy deployment to support EPAS flavor.

- Update documentation to use latest BDR Always-ON architecture diagram

## v21.2 (2021-06-02)

### Notable changes

- Install under /opt/EDB/TPA (with a symlink from /opt/2ndQuadrant/TPA
  for backwards compatibility)

- Delay the activation of the `synchronous_standby_names` setting until
  all expected replicas are running (but this applies only if you set it
  directly under `vars`, and not under `postgres_conf_settings`)

### Minor changes

- Improve handling of custom commands by `tpaexec help`

- Improve the build process for `tpa/xxx` docker images

- Improve installation instructions, especially for MacOS X users

- Enable etcd consensus layer support for HARP on RHEL/CentOS 7, with
  support for other platforms in development

- Avoid generating duplicate entries in /etc/hosts when changing the IP
  addresses for existing instances

- Set `server_login_retry` to 0 by default for pgbouncer to avoid a 15s
  delay during failover

### Bugfixes

- Fix "Cannot find a valid baseurl for repo: pgdg94" errors after the
  upstream removal of the pgdg94 repository

- Install edb-asNN-server package to obtain pg_receivewal when using
  Barman with EPAS (this is a workaround until pg_receivewal is made
  available with the client package, as with Postgres)

- Fix errors about haproxy_backend_servers not being defined on clusters
  without haproxy instances

- Fix some errors during deployment when TPAexec is installed in a path
  that contains spaces

- Fix "template error while templating string" error when installing
  EPAS on Debian

## v21.1 (2021-03-01)

This release has experimental support for deploying EPAS (EDB Postgres
Advanced Server) for internal use, and the next release will make this
feature generally available.

### Notable changes

- The new `tpaexec pool-disable-server` and `pool-enable-server`
  commands can be used to temporarily remove a BDR server from the
  HAProxy server pool for maintenance (e.g., rehydration) and add it
  back afterwards (see docs/tpaexec-server-pool.md for details). This
  process works like rolling updates by default, and will wait for any
  active sessions to end and new connections to be routed to another
  server by pgbouncer and haproxy.

### Minor changes

- Adapt to new repository filenames/section names CentOS 8 (fixes
  "Cannot find a valid baseurl for repo: AppStream" errors)

- Set `ssl_min_protocol_version = 'TLSv1.2'` wherever supported
  (Postgres 12 and above, or 2ndQPostgres 11 and above)

- Improve installation instructions, especially for MacOS X users

- Make `tpaexec relink` add links from an existing cluster to any new
  commands and tests that are applicable to its architecture

### Bugfixes

- Stop postgres messages from falling through to be logged to
  /var/log/syslog

- Fix incorrect detection of PGDATA and Postgres instance roles during
  rehydration, which led to failures while running `initdb` or `repmgr
  standby clone` or creating users (spurious failures, in that running
  deploy again would fix the problem)

- Fix errors about `my_hosts_lines` and other variables being undefined
  when running `tpaexec rehydrate`

- Reject empty lines in `--hostnames-from` input file (which would
  result in "list object has no element 2" exceptions from `tpaexec
  configure`)

- Fix default systemd target for docker containers, so that restarting
  the container correctly restarts all of its services

- Specify postgres_host and postgres_port when running pgbench

## v20.11 (2020-12-15)

### Minor changes

- Pin barman-cli/python3-barman to 2ndQuadrant repositories

- Accept `repmgr_conf_settings` to append extra lines to repmgr.conf

- Improve TPA_DIR detection when realpath(1) is not installed

### Bugfixes

- Use pkill instead of killall, which is deprecated

- Allow for `public_ip` to be set to `null` rather than undefined (to
  accommodate default ec2.py output for instances with no public IP)

- Always set TMPDIR when calling git clone (to avoid "permission denied"
  errors when cloning git submodules)

- Ensure barman_home exists if it is set to a non-standard location

## v20.10 (2020-11-13)

### Minor changes

- On AWS EC2 instances, create a symbolic link from /usr/local/bin/aws
  to the installed awscli executable (for use in scripts)

- Create the builtin tpa/xxx docker images in a single step, rather than
  building a -base image first (but custom two-stage builds are still
  supported)

- Accept `postgres_hba_local_auth_method: md5` setting to replace the
  default `local all all peer` line in pg_hba.conf

- Use latest PGDG YUM repo RPMs from /pub/repos/yum/reporpms

- Remove deprecated replication_type setting from repmgr.conf

- Exclude python3-barman package from PGDG repository (we should always
  use the version from the 2Q repositories)

- Improve config.yml validation

### Bugfixes

- Fix a problem with cloning an HTTPS repository with ssh submodules
  that caused `fatal: cannot exec '/tmp/tmpXXXXXXXX': Permission denied`
  errors on Docker containers (e.g., when updating pglogical_dump)

- Fix python2.7 interpreter discovery on Ubuntu 18.04/bionic: if
  preferred_python_interpreter was unset, the earlier code would
  install Python 3 but try to use Python 2

- Fix a problem with running pgbouncer and Postgres on the same host,
  where pgbouncer was not able to authenticate via md5

- Ensure `tpaexec configure xyz/` does not create config.yml with an
  empty cluster_name

- Set wal_keep_size instead of wal_keep_segments for Postgres 13+

- Disable unattended-upgrades on Debian and Ubuntu

## v20.9 (2020-09-22)

### Notable changes

- Improve documentation (under "Customisations", start with "Cluster
  configuration" and "Instance configuration")

- Support setting `password_encryption: scram-sha-256` (default for new
  clusters, but existing clusters will remain unchanged unless you set
  the variable explicitly)

- Add new `tpaexec show-password /path/to/cluster username` and
  `tpaexec store-password /path/to/cluster username [--random]`
  commands to manage passwords for postgres_users

- Add a `postgres_locale` setting, defaulting to the target instance's
  LC_ALL/LANG setting (or en_US.UTF-8 otherwise), which is used to set
  the initdb-time default for the cluster

- Require that the BDR database have the same collation (LC_COLLATE)
  across all instances in the same bdr_node_group

- Add a `manage_ssh_hostkeys` variable for bare instances (default: no)
  that controls the installation of generated host keys and known_hosts
  entries on the cluster (see docs/platform-bare.md for details)

- Default to using `private_ip` for communication between instances in
  the cluster (e.g., for Postgres replication and backups) while using
  the `public_ip` to access the instances during deployment, for bare
  instances with both `private_ip` and `public_ip` set

- Add support for building Docker clusters from source using
  bind-mounted --local-source-directories and a shared ccache

- Improve deployment speed in various ways

### Minor changes

- Support pglogical v2 publication/subscription configuration

- Use volatile subscriptions by default on docker containers

- Add eu-north-1 to aws_known_regions

- Add a `preload_extensions` list to declare extensions that need an
  entry in shared_preload_libraries if included in postgres_extensions

- Don't uninstall any packages by default (default_unwanted_packages)

- Account for grubby storing kernelopts in /boot/grub2/grubenv

- Ensure Postgres is restarted when new packages are installed

- Move BDR-specific initialisation code into pgbench/init; callers can
  now include pgbench/init directly from their own hooks/commands/tests
  for BDR clusters, without having to duplicate lock timeout management
  from pgbench-bdr.yml

- Only add required lines to /etc/hosts, rather than generating the file
  from scratch

- Accept optional per-volume `fstype`, `fsopts`, `mountopts`,
  `readahead`, `owner`, `group`, `mode` vars for volumes

- Adapt to grubby storing kernelopts in /boot/grub2/grubenv on RHEL8

- Improve handling of LUKS-encrypted volumes

### Bugfixes

- Generate a valid Vagrantfile even for hostnames with hyphens

- Patch `TypeError: a bytes-like object is required, not 'str'` errors
  when using Boto with an https_proxy set (run `tpaexec setup`)

- Disable pgbench test for BDR v1/v2 clusters

- Fix haproxy syslog logging configuration

## v20.8 (2020-08-20)

### Bugfixes

- Fix "ReadOnlySqlTransaction" error on replicas from postgres/cleanup

- Fix "max_worker_processes" error during rehydration of replicas

### Other changes

- Accept `TPA_GIT_CREDENTIALS=username:access_token` in the local
  environment to clone https:// repository URLs when building from
  source (+ `TPA_GIT_CREDENTIAL_STORE=/path/to/.gitcredentials`)

## v20.7 (2020-08-20)

### Notable changes

- Add support for multiple distributions on Docker via
  `tpaexec configure … --os Debian/Ubuntu/RedHat`

- Complete support for RHEL/CentOS 8 across architectures

- Allow setting `postgres_conf_dir` to separate configuration files
  from PGDATA

- Add support for HARP with BDR as the consensus mechanism

- Add new `postgres_users` and `postgres_databases` settings to
  create users and databases during deployment

- Add declarative configuration for pglogical replication through
  `publications` and `subscriptions` of `type: pglogical`

- Add a `tpaexec relink` command to repair dangling symlinks into
  TPA_DIR from within a cluster directory

- Add many new and exciting default hostnames beginning with 'u'

### Bugfixes

- Avoid running out of memory while setting SELinux context for PGDATA

- Always prefer to install 2ndQuadrant barman packages on Debian/Ubuntu

- Revert workarounds for problems with the PGDG yum repository that have
  been fixed upstream

- Avoid installing pgbouncer from the EPEL repo because of a broken
  dependency on python-psycopg2

- Fix some inconsistencies with --overrides-from that prevented certain
  generated settings from being overriden at configure time

## v20.6 (2020-07-10)

### Bugfixes

- Fix "No commands may be run on the BDR supervisor database" during
  fact discovery on BDR v1/v2 clusters

## v20.5 (2020-07-10)

### Notable changes

- Remove the CAMO2x2 architecture (use BDR-Always-ON instead)

- Numerous internal improvements

### Minor changes

- Update default haproxy_package_version to 1.9.15

- Disable invalid pgdg11-updates-debuginfo repository for RHEL8; deploy
  with `-e '{"postgres_debug_packages":{"postgresql":{"RedHat":[]}}}'`
  if required until the problem is fixed upstream

- Restore support for repmgr to create physical replicas in BDR clusters

- Exclude psycopg2 packages from PGDG yum repositories

### Bugfixes

- When adding a new instance to a BDR cluster, ensure that some other
  existing instance is marked as the first_bdr_primary; otherwise the
  new instance would not join the existing cluster (RT67887)

- Create the pgbouncer schema on only one BDR instance, to avoid a DDL
  lock acquisition timeout during deployment

- Generate a valid restore_command when multiple backup servers are
  specified for an instance

### Porting notes

- The 'common' role has been removed, and its functionality absorbed
  into the 'sys' role

## v20.4 (2020-04-30)

This release of TPAexec would have been v9.4, but has been renumbered in
order to avoid any confusion with Postgres version numbers.

### Notable changes

- Adapt to various PGDG YUM repository layout changes and enable
  pgdg-common repository by default

- Update expired 2ndQuadrant APT repository signing keys on existing
  Debian/Ubuntu clusters

- Create unprivileged docker containers by default (but you can still
  set `privileged: yes` on the instance in config.yml)

- Add basic support for creating user-defined Docker networks and
  attaching containers to them

- Calculate pgbouncer_max_client_conn based on max_connections

### Bugfixes

- Fix python-psycopg2 vs python2-psycopg2 package conflict when
  installing barman-cli

- Fix selinux dependency problems ("Failed to detect selinux python
  bindings")

- Correctly handle `ssh_key_file: /path/to/id_xxx` as well as
  `ssh_key_file: ~/.ssh/id_rsa` settings in config.yml

- Ensure that pgbouncer.ini changes cause a restart when using
  `--tags pgbouncer`

- Avoid trying to create haproxy users when there are no haproxy
  instances in a cluster

- Silence some inapplicable Ansible warnings

- Fix ec2 inventory caching problem

- Correctly bundle version-specific Python dependencies (e.g.,
  MarkupSafe) in tpaexec-deps

## v9.3 (2020-03-10)

### Minor changes

- Allow haproxy.cfg default-server/server options to be customised via
  new variables: haproxy_default_server_extra_options (for an haproxy
  instance) and haproxy_server_options (for a Postgres instance)

- Allow pgbouncer_databases setting to include pool_size and other
  options without specifying a complete DSN

- Rename haproxy_backends to haproxy_backend_servers (but the former
  name continues to be accepted for backwards compatibility)

- Allow haproxy_bind_address to be changed

- Add a new post-repo hook that is executed after package repositories
  are configured, but before packages are installed

### Bugfixes

- Fix problem in v9.2 with extra_postgres_extensions being undefined

## v9.2 (2020-03-05)

This release requires `tpaexec setup` to be rerun after installation.

### Major changes

- Require Python 3.6+ on the machine running tpaexec

- Optionally support Python 3 (`preferred_python_version: python3`) on
  target instances that run one of the following distributions:

  * Debian 9 (stretch)
  * Debian 10 (buster)
  * Ubuntu 16.04 (xenial)
  * Ubuntu 18.04 (bionic)

- Existing clusters continue to work unmodified with Python 2.7

- Newly-configured clusters use Python 3 by default wherever available;
  set `preferred_python_version: python2` to undo this

- Running `tpaexec setup` will now create $TPA_DIR/tpa-venv (it is
  safe to remove the old tpa-virtualenv directory)

- Require 2ndQuadrant ansible to be installed via `tpaexec setup`, and
  ignore any other Ansible installation in $PATH

- Enable HTTP-based queue checks for haproxy if the Platypus extension
  is available on the backend Postgres servers (this fixes the SELinux
  limitation mentioned in the v9.1 release notes)

### Upgrade note

If you are using tpaexec v9.2 to upgrade an existing cluster running
BDR-EE 3.6.14 or earlier with 2ndQPostgres, you must first remove the
`postgresql11-devel` package from target instances before you run
`tpaexec update-postgres`. This is because the 3.6.15/3.6.16 stack
releases add an LLVM-related dependency (llvm-toolset-7-clang) that
cannot be satisifed by the default package repositories.

Instead of removing the package, `yum install centos-release-scl` (on
CentOS) or `yum-config-manager --enable rhel-server-rhscl-7-rpms` (on
RHEL) may be enough to make the update succeed even with
postgresql11-devel installed.

We expect to fix this problem in a future release of the BDR stack.

## v9.1 (2020-01-20)

This release requires `tpaexec setup` to be rerun after installation.

### Notable changes

- Update 2ndQuadrant Ansible to v2.8 (`tpaexec setup` will upgrade)

- Introduce additional checks through haproxy to avoid stale reads after
  failover for CAMO instances (RM11664); this does not work with SELinux
  enabled on the haproxy server (will be fixed in the next release)

### Minor changes

- Wait for reachability checks to pass only during deploy, not custom
  commands (which become a little faster with this change)

- Various improvements to source builds, including the ability to build
  from source on Docker containers

- Don't set net.ipv4.ip_forward by default, only when required

- Require haproxy 1.9.13 instead of 1.9.7 (security fixes)

- Various Python 3 compatibility changes (the next release will be fully
  Python 3 compatible)

- Various testing improvements

### Bugfixes

- Ensure that a replica does not have max_worker_processes < the primary

- Ignore repmgr_redirect_pgbouncer if there are no pgbouncer instances

- Don't set bdr_node_camo_partner for logical standby instances

## v9.0 (2019-12-03)

### Notable changes

- Support rolling update procedure for BDR-Always-ON

- Add new postgres-pre-update and postgres-post-update hooks

### Minor changes

- Allow custom `haproxy_port` to be set

- Allow custom `archive_command` to be set

- Remove file descriptor limit for pgbouncer

- Disable repmgrd by default on BDR instances

### Bugfixes

- Remove an unnecessary postgres restart after first deploy

- Disable pgdgNN repository entries in yum.repos.d that do not
  correspond to the desired postgres_version

- Install postgresql client libraries before installing Barman and
  pgbouncer (to avoid version mismatches)

- Fix quoting in repmgr.conf for repmgr v5

## v8.4 (2019-09-23)

### Minor changes

- Add new pre-initdb hook

- Ignore extra_float_digits by default in pgbouncer

### Bugfixes

- Fix BDRv1 repository installation problem

## v8.3 (2019-08-29)

This release requires `tpaexec setup` to be rerun after installation.

### Notable changes

- Set max_prepared_transactions to 16 by default for BDR clusters
  (requires Postgres restart); 2PC is required by CAMO and eager
  all-node replication

- Set synchronous_commit after BDR initialisation for BDR clusters

- Enable EBS volume encryption at rest by default for new clusters

- Configure HAproxy peering within a location by default

### Minor changes

- Accept `etc_hosts_lines` list variable setting to completely control
  /etc/hosts contents

- Retrieve and set bdr_node_id during BDR initialisation

### Bugfixes

- Fix incorrect generation of /boot/grub2/grub.cfg on RedHat systems

- Correctly limit explicit subnet associations of AWS route tables to
  those subnets used by the cluster within a region

- Correctly remove AWS security groups for the cluster during
  deprovisioning

- Respect ProxyCommand (and any other ssh options) set in the inventory
  when waiting for hosts to be reachable via ssh

- Correctly quote string arguments in repmgr.conf

- Accept argument-less SQL queries with embedded literal % characters
  (internal)

## v8.2 (2019-08-08)

### Notable changes

- Accept bdr_node_group_options hash to set bdr.create_node_group()
  options

- Accept `log_destination: stderr` setting to log directly to
  /var/log/postgresql/postgres.log (without going through rsyslog)

- Accept `repmgr_redirect_pgbouncer` setting to reconfigure pgbouncer
  on repmgr failover events

- Testing improvements

### Minor changes

- Accept post_backup_script setting for barman

- Accept log_min_messages setting for Postgres conf.d

- Accept top-level use_ssh_agent setting (omit IdentitiesOnly)

- Accept repmgr_reconnect_{attempts,interval} settings for repmgr.conf

### Bugfixes

- Don't set ssl_ca_file to the default self-signed certificate if
  ssl_cert_file is explicitly set

- Don't generate /etc/cron.d/some.fq.dn because cron will ignore files
  under /etc/cron.d that have dots in the name

- Never try to reuse elastic IPs on AWS (for security reasons)

- Suppress unnecessary changed notifications for various tasks

## v8.1 (2019-07-20)

### Notable changes

- Support user-supplied TLS client certificates for authentication
  (RT65159)

- Allow setting `hba_force_certificate_auth: yes` on any Postgres
  server instance to force TLS certificate authentication for clients
  instead of password authentication

- Allow setting `postgres_service_environment` to set environment
  variables in the postgres service unit file

- Support new postgres-config and postgres-config-final hooks

- Improvements for source builds

- Testing improvements

### Bugfixes

- Invoke postgres/facts from init only if postgres is running

- Ensure correct ordering of shared_preload_libraries

## v8.0 (2019-06-20)

### Notable changes

- Improve the BDR replication set configuration process

- Enable debugging by default when building Postgres from source

- Numerous testing improvements

- Support for Barman 2.8

- New `--hostnames-unsorted` configure option to avoid sorting
  hostnames when assigning them to instances

### Bugfixes

- Remove unused 2ndQuadrant repository configuration files

- When redeploying on an existing cluster, use PG_VERSION to derive
  postgres_version if the latter is not explicitly set in config.yml

- Don't remove the default replication set from the BDR subscription
  (this breaks DDL replication)

- Fix incorrect generation of /etc/default/grub

## v7.9 (2019-05-09)

### Bugfixes

- Revert an unintended change to the default pgbouncer_backend
  configuration

## v7.8 (2019-05-08)

### Notable changes

- Allow setting `bdr_node_name` in an instance's vars to change the
  name of the BDR node (the default remains to use the instance's name)

- Require haproxy 1.9.7 (for which packages are available from the
  2ndQuadrant package repository)

- Create an haproxy role (with NOLOGIN) to eliminate haproxy check
  messages from the Postgres log

- Change default postgres_version to 11 for new clusters

- Numerous internal testing improvements

## v7.7 (2019-04-22)

### Notable changes

- Make the `tpaexec test` command take an optional test name, and
  provide infrastructure for custom tests

- Adapt to BDR-Always-ON v5 architecture changes

### Minor changes

- Allow optional branch names (git refs) to be specified with
  `--install-from-source 2ndqpostgres:2QREL_11_STABLE_dev …`

- Accept a list of options in `postgres_extra_configure_opts` to
  append to the Postgres configure invocation (backwards-compatible
  with existing usage of `postgres_configure_opts`)

### Bugfixes

- Try to apply desired transparent hugepage settings immediately, not
  only after a reboot

- Correctly show build failures when installing extensions from source

## v7.6 (2019-04-12)

### Notable changes

- Use new PGDG repository RPM location after breaking change upstream

- Accept `--install-from-source 2ndqpostgres pglogical3 bdr3` as a
  configure option to set up a cluster built from source

### Bugfixes

- Correctly remove provisioned AWS route tables during deprovision

- Correctly override postgres_bin_dir for clusters built from source

- Change pg_receivwal invocation to make
  `barman receive-wal --stop servername` work reliably

## v7.5 (2019-04-04)

You must run `tpaexec setup` after installing the release packages.

### Notable changes

- Support NVMe instance store volumes on AWS EC2 (in addition to EBS
  volumes, which were already supported)

- Allow 'bare' instances to have FQDNs

- CAMO configuration updates

### Bugfixes

- Correctly setup cascading replication with repmgr 4.2

- Correctly handle non-standard postgres_port settings

- Don't install the sudo package if a sudo binary is available

- Fall back to bzip2 or gzip for Barman compression if pigz is not
  available

- Allow pgbouncer_port to be set to override the default

- Create pgbouncer.get_auth() function in existing databases

- Improved handling of debuginfo packages on Debian

## v7.4 (2019-02-20)

### Notable changes

- Add `--overrides-from a.yml …` configure option to set variables
  like cluster_tags and cluster_vars in the generated config.yml

### Bugfixes

- Don't require --distribution with --platform bare

- Don't install awscli on clusters without AWS instances

- Allow synchronous_commit to be overriden for CAMO instances (instead
  of always forcing it to remote_apply)

## v7.3 (2019-02-07)

### Notable changes

- Improve the `tpaexec update-postgres` command to update all
  Postgres-related packages, and make it available on BDR-based
  architectures

- Enable TLS by default between pgbouncer ↔ haproxy ↔ postgres

- Add --enable-camo configure option for BDR-Simple and BDR-Always-ON

- Avoid installing dl/default/release if tpa_2q_repositories is set to
  [] explicitly (aside from being able to set {apt,yum}_repository_list
  to [] to suppress other external repositories)

- Revised pgbench schedule for `tpaexec test`, with separate
  pgbench-postgres and pgbench-bdr stages (== tags)

### Bugfixes

- Various haproxy/pgbouncer configuration tweaks

- Fix errors in initialisation of BDR logical standby instances

- Further changes to avoid version-specific flock(1) invocations

### Porting notes

- We write instance variables only to host_vars/*/01-instance_vars.yml,
  and remove 02-topology.yml and 03-volumes.yml during provisioning

- Individual platforms can use simpler code to set instance_vars now

## v7.2 (2019-01-08)

### Major changes

- Allow additional artifacts (files, archives, directories) to be
  installed on instances (via `artifacts`)

- Support building extensions from source (via `install_from_source`)

### Bugfixes

- Fix flock(1) compatibility problems that resulted in complaints about
  not being able to find files like xxx_password.yml or id_xxx.pub

### Other notable changes

- Add --extra{,-optional}-packages configure arguments

- The `tpaexec info {platforms,architectures}` command now lists the
  actual contents of the corresponding directories

- Support wildcard entries directly in s3_uploads

## v7.1 (2018-12-12)

### Major changes

- Support for CAMO2x2 architecture with BDR-EE 3.4.0 and 2ndQPostgres 11
  (with local replication of deletes as an option).

- Support for named locations in config.yml

### Bugfixes

- Fixes for some Barman and repmgr problems

## v7.0 (2018-11-14)

In this release, TPAexec goes from v3.1 to v7.0 as a precaution to avoid
creating any confusion with the similar version numbers for BDR and the
BDR-Always-ON architecture. This release would otherwise have been v3.2.

### Major changes

- Multi-platform support in `tpaexec configure`

- Experimental support for Vagrant, Docker, and lxd platforms

- Allow instances to be backed up to multiple Barman servers in parallel

- Add hooks/pre-deploy.yml and hooks/post-deploy.yml (included during
  deployment if they exist)

### Bugfixes

- Install correct rsyslog/logrotate rules for local logging
- Support EC2 instances with NVME devices

### Porting notes

- deploy.yml should now «include_role: name=sys» instead of including
  the various sys/* roles one by one

### Other notable changes

- Enable repmgr monitoring_history
- Allow uploading additional files to S3 during provisioning
- Add 'hba_force_hostssl' to force hostssl lines in pg_hba.conf
- Revoke superuser privileges from the pgbouncer user
- Set repmgr_location only if explicitly requested
- Allow - in cluster names
- Set default archive_timeout of 6h
- Allow event_notification{s,_command} to be set in repmgr.conf

## v3.1 (2018-09-17)

### Major changes

- Added support for deployment architectures.
  See `tpaexec info architectures` for details.

- Added `tpaexec configure` command that takes an architecture
  name and various options and generates config.yml and deploy.yml for
  a new cluster.

- New BDR3-Always-ON and BDR-Simple architectures

- New `tpaexec test` command

- New `tpaexec setup` command to setup a virtualenv and install Python
  dependencies automatically (the virtualenv will also be automatically
  activated when using tpaexec)

- New `tpaexec selftest` command to check the TPAexec installation.

- Automatic package builds

### Bugfixes

- Properly handle stopped instances in the inventory, so that re-running
  provision does not create duplicates for instances that happen to not
  be running at the time (f0cb0ea)
- Properly handle an AWS race condition that resulted in "Invalid IAM
  Instance Profile name" errors during provisioning (f37de54)
- Make deployment fail if ec2.py fails; depends on a patch available in
  2ndQuadrant ansible (55a4fd3)
- Properly reassemble EBS RAID arrays after rehydration.
- Correctly handle (ignore) empty lines in /proc/$pid/status
- Correctly restart repmgrd after changing repmgr.conf
- Make sure coredumps are generated properly.
- Fixed RHEL issue `"Aborting, target uses selinux but python bindings
  (libselinux-python) aren't installed!"` (f245e99)
- Fixed tpaexec rehydrate failing with `"hostvars[''node-b'']\" is undefined`
  (b74bfa2)
- Fixed repmgrd failing to start for repmgr 4.1.0 on CentOS/RedHat (aee5862)
- Fixed repmgr not quite attaching replica on RHEL systems.

### Porting notes

- Instead of applying role 'postgres/final' on postgres instances,
  deploy.yml files should now apply role 'final' to all instances.
- If a volume in config.yml has vars "volume_for" and "mountpoint" both
  set, the latter will now take precedence over the default translation
  based on volume_for. Setting a mountpoint without setting volume_for
  is strongly discouraged (for postgres_data and barman_data volumes).
  Setting volume_for alone is still fine.

### Other notable changes

- Extensive documentation updates
- Initial LXD platform support
- Support postgres/repmgr/barman package version selection (6e904c8)
  via `tpaexec configure … --postgres-package version`
- When generating restore_command, prefer the closest Barman server
  (i.e., one in the same region) if there's more than one available
- Deprecate ec2_ami_user and cluster_ssh_user in favour of setting
  "vars: ansible_user: xxx" in instance_defaults (a9c30e1)
- Make cluster_tags optional. Owner is now automatically set to the
  current user's login name, and can be overriden with --owner
- Deprecate cluster_network{,s} (which was used only to generate
  pg_hba.conf) while maintaining backwards compatibility
- Allow instance settings to be exported as instance vars (2a6e060)
- Allow instance_defaults to specify default_volumes for all instances
- Include traceback information on module failure in various cases
- Remove ansible-cluster and ansible-cluster-playbook in favour of
  `tpaexec cmd` and `tpaexec playbook`
- New `tpaexec start-postgres` and `tpaexec stop-postgres` commands
  for clusters that use LUKS-encrypted volumes
- New `tpaexec switchover clustername nodename` command for M1
  clusters
- The `provision`, `deploy`, `deprovision`, and `rehydrate`
  commands are replaced by `tpaexec provision` etc.
- Various changes related to packaging

## v3.0 (2018-06-05)

TPA has switched from vYYYY.MM.NN to vM.N version numbers.

The new version numbers are not semantic versions. They do not imply
anything about compatibility or incompatibility, nor an intention to
maintain multiple branches with varying features or maturity.
