# TPA release notes

Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

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
