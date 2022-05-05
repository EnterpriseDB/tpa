# TPA release notes

© Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

## v22.14 (unreleased)

### Notable changes

- Change the default HARP v2 consensus protocol from etcd to bdr

  This does not affect existing clusters that are using etcd (even if
  they do not have harp_consensus_protocol set explicitly)

- Require Docker CE v20.10+

  There are a number of problems on older versions of Docker that we can
  neither fix, nor work around. We now require the latest major release
  of Docker CE.

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

### Bugfixes

- Check that TPA_2Q_SUBSCRIPTION_TOKEN is set when needed

  Fixes a 403 error during the repository in clusters configured to use
  Postgres Extended (--2q) without setting --2Q-repositories and without
  providing a token.

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
