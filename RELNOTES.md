# TPA release notes

## HEAD (not yet released)

### Major changes

- Added support for deployment architectures.
  See ``tpaexec info architectures`` for details.

- Added ``tpaexec configure`` command that takes an architecture
  name and various options and generates config.yml and deploy.yml for
  a new cluster.

- New BDR3-Always-ON and BDR-Simple architectures

- Experimental support for Vagrant, Docker, and lxd platforms

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
