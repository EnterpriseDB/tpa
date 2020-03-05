# TPA release notes

Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

## v9.3 (unreleased)

[In prep.]

## v9.2 (2020-03-05)

This release requires ``tpaexec setup`` to be rerun after installation.

### Major changes

- Require Python 3.6+ on the machine running tpaexec

- Optionally support Python 3 (``preferred_python_version: python3``) on
  target instances that run one of the following distributions:

  * Debian 9 (stretch)
  * Debian 10 (buster)
  * Ubuntu 16.04 (xenial)
  * Ubuntu 18.04 (bionic)

- Existing clusters continue to work unmodified with Python 2.7

- Newly-configured clusters use Python 3 by default wherever available;
  set ``preferred_python_version: python2`` to undo this

- Running ``tpaexec setup`` will now create $TPA_DIR/tpa-venv (it is
  safe to remove the old tpa-virtualenv directory)

- Require 2ndQuadrant ansible to be installed via ``tpaexec setup``, and
  ignore any other Ansible installation in $PATH

- Enable HTTP-based queue checks for haproxy if the Platypus extension
  is available on the backend Postgres servers (this fixes the SELinux
  limitation mentioned in the v9.1 release notes)

### Upgrade note

If you are using tpaexec v9.2 to upgrade an existing cluster running
BDR-EE 3.6.14 or earlier with 2ndQPostgres, you must first remove the
``postgresql11-devel`` package from target instances before you run
``tpaexec update-postgres``. This is because the 3.6.15/3.6.16 stack
releases add an LLVM-related dependency (llvm-toolset-7-clang) that
cannot be satisifed by the default package repositories.

Instead of removing the package, ``yum install centos-release-scl`` (on
CentOS) or ``yum-config-manager --enable rhel-server-rhscl-7-rpms`` (on
RHEL) may be enough to make the update succeed even with
postgresql11-devel installed.

We expect to fix this problem in a future release of the BDR stack.

## v9.1 (2020-01-20)

This release requires ``tpaexec setup`` to be rerun after installation.

### Notable changes

- Update 2ndQuadrant Ansible to v2.8 (``tpaexec setup`` will upgrade)

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

- Allow custom ``haproxy_port`` to be set

- Allow custom ``archive_command`` to be set

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

This release requires ``tpaexec setup`` to be rerun after installation.

### Notable changes

- Set max_prepared_transactions to 16 by default for BDR clusters
  (requires Postgres restart); 2PC is required by CAMO and eager
  all-node replication

- Set synchronous_commit after BDR initialisation for BDR clusters

- Enable EBS volume encryption at rest by default for new clusters

- Configure HAproxy peering within a location by default

### Minor changes

- Accept ``etc_hosts_lines`` list variable setting to completely control
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

- Accept ``log_destination: stderr`` setting to log directly to
  /var/log/postgresql/postgres.log (without going through rsyslog)

- Accept ``repmgr_redirect_pgbouncer`` setting to reconfigure pgbouncer
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

- Allow setting ``hba_force_certificate_auth: yes`` on any Postgres
  server instance to force TLS certificate authentication for clients
  instead of password authentication

- Allow setting ``postgres_service_environment`` to set environment
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

- New ``--hostnames-unsorted`` configure option to avoid sorting
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

- Allow setting ``bdr_node_name`` in an instance's vars to change the
  name of the BDR node (the default remains to use the instance's name)

- Require haproxy 1.9.7 (for which packages are available from the
  2ndQuadrant package repository)

- Create an haproxy role (with NOLOGIN) to eliminate haproxy check
  messages from the Postgres log

- Change default postgres_version to 11 for new clusters

- Numerous internal testing improvements

## v7.7 (2019-04-22)

### Notable changes

- Make the ``tpaexec test`` command take an optional test name, and
  provide infrastructure for custom tests

- Adapt to BDR-Always-ON v5 architecture changes

### Minor changes

- Allow optional branch names (git refs) to be specified with
  ``--install-from-source 2ndqpostgres:2QREL_11_STABLE_dev …``

- Accept a list of options in ``postgres_extra_configure_opts`` to
  append to the Postgres configure invocation (backwards-compatible
  with existing usage of ``postgres_configure_opts``)

### Bugfixes

- Try to apply desired transparent hugepage settings immediately, not
  only after a reboot

- Correctly show build failures when installing extensions from source

## v7.6 (2019-04-12)

### Notable changes

- Use new PGDG repository RPM location after breaking change upstream

- Accept ``--install-from-source 2ndqpostgres pglogical3 bdr3`` as a
  configure option to set up a cluster built from source

### Bugfixes

- Correctly remove provisioned AWS route tables during deprovision

- Correctly override postgres_bin_dir for clusters built from source

- Change pg_receivwal invocation to make
  ``barman receive-wal --stop servername`` work reliably

## v7.5 (2019-04-04)

You must run ``tpaexec setup`` after installing the release packages.

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

- Add ``--overrides-from a.yml …`` configure option to set variables
  like cluster_tags and cluster_vars in the generated config.yml

### Bugfixes

- Don't require --distribution with --platform bare

- Don't install awscli on clusters without AWS instances

- Allow synchronous_commit to be overriden for CAMO instances (instead
  of always forcing it to remote_apply)

## v7.3 (2019-02-07)

### Notable changes

- Improve the ``tpaexec update-postgres`` command to update all
  Postgres-related packages, and make it available on BDR-based
  architectures

- Enable TLS by default between pgbouncer ↔ haproxy ↔ postgres

- Add --enable-camo configure option for BDR-Simple and BDR-Always-ON

- Avoid installing dl/default/release if tpa_2q_repositories is set to
  [] explicitly (aside from being able to set {apt,yum}_repository_list
  to [] to suppress other external repositories)

- Revised pgbench schedule for ``tpaexec test``, with separate
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
  installed on instances (via ``artifacts``)

- Support building extensions from source (via ``install_from_source``)

### Bugfixes

- Fix flock(1) compatibility problems that resulted in complaints about
  not being able to find files like xxx_password.yml or id_xxx.pub

### Other notable changes

- Add --extra{,-optional}-packages configure arguments

- The ``tpaexec info {platforms,architectures}`` command now lists the
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

- Multi-platform support in ``tpaexec configure``

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
  See ``tpaexec info architectures`` for details.

- Added ``tpaexec configure`` command that takes an architecture
  name and various options and generates config.yml and deploy.yml for
  a new cluster.

- New BDR3-Always-ON and BDR-Simple architectures

- New ``tpaexec test`` command

- New ``tpaexec setup`` command to setup a virtualenv and install Python
  dependencies automatically (the virtualenv will also be automatically
  activated when using tpaexec)

- New ``tpaexec selftest`` command to check the TPAexec installation.

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
  via ``tpaexec configure … --postgres-package version``
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
  ``tpaexec cmd`` and ``tpaexec playbook``
- New ``tpaexec start-postgres`` and ``tpaexec stop-postgres`` commands
  for clusters that use LUKS-encrypted volumes
- New ``tpaexec switchover clustername nodename`` command for M1
  clusters
- The ``provision``, ``deploy``, ``deprovision``, and ``rehydrate``
  commands are replaced by ``tpaexec provision`` etc.
- Various changes related to packaging

## v3.0 (2018-06-05)

TPA has switched from vYYYY.MM.NN to vM.N version numbers.

The new version numbers are not semantic versions. They do not imply
anything about compatibility or incompatibility, nor an intention to
maintain multiple branches with varying features or maturity.
