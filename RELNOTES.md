# TPA release notes

## HEAD (not yet tagged)

### Major changes

- Added support for deployment architectures.
  See ``tpaexec info architectures`` for details.

- Added ``tpaexec configure`` command that takes an architecture
  name and various options and generates config.yml and deploy.yml for
  a new cluster.

- Added BDR3 deployment support

- New ``tpaexec test`` command

- New ``tpaexec setup`` command to setup a virtualenv and install Python
  dependencies automatically (the virtualenv will also be automatically
  activated when using tpaexec)

- Automatic package builds

### Bugfixes

- Properly handle stopped instances in the inventory, so that re-running
  provision does not create duplicates for instances that happen to not
  be running at the time (f0cb0ea)
- Properly handle an AWS race condition that resulted in "Invalid IAM
  Instance Profile name" errors during provisioning (f37de54)
- Make deployment fail if ec2.py fails; depends on a patch available in
  2ndQuadrant ansible (55a4fd3)
- Correctly handle (ignore) empty lines in /proc/$pid/status
- Correctly restart repmgrd after changing repmgr.conf
- Make sure coredumps are generated properly

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
- Various changes related to packaging

## v3.0 (2018-06-05)

TPA has switched from vYYYY.MM.NN to vM.N version numbers.

The new version numbers are not semantic versions. They do not imply
anything about compatibility or incompatibility, nor an intention to
maintain multiple branches with varying features or maturity.

## v2018.06 (2018-06-05)

Notable changes:

- Top-level tpaexec command.

- Framework for multiple platform support, with each instance declaring
  its «platform: xxx» in config.yml.

- Centralise all repository management in common/pkg. We now install
  PGDG and the 2Q repository by default. (The 2ndQPostgres repository
  will be added back when it is available again.)

- Location-independent commands (i.e., you can run $TPA_DIR/bin/tpaexec
  from anywhere, not just cd $TPA_DIR && bin/tpaexec).

- Support repmgr4 (installed from source or package).

- Allow common instance_defaults[] to be specified in config.yml, with
  the option to override them in instances[] if needed.

- Better support to disable THP system-wide.

- Better support for training clusters.

- Ansible compatibility fixes.

- Documentation updates.

- AWS:

  - Separate routing table and igw creation from VPC creation.
  - Support for «-e use_cached_vars=1» during provisioning.
  - More comprehensive cluster deprovisioning support.

Bugfixes:

- Fix a bug with repmgr/final dying on non-Postgres instances
- Fix some bugs with volume_for/mountpoint declarations
- Fix repmgr and postgres service dependencies
- Don't overwrite .pgpass each time
- Make sure /etc/rc.local is used

## v2017.10 (2017-10-05)

Features:

- We override the role/upstream settings in config.yml with information
  discovered by querying the cluster, thereby adapting gracefully to
  changes after failover/switchover.

- We no longer try to use Distribution-specific locations and setup
  tools (e.g., pg_createcluster), but instead use initdb to initialise
  PGDATA and install our own service files for Postgres.

- Allow volumes to be retained and reattached to new instances to
  support re-deployments on a new instance with old data volumes.

- Feature parity for postgres/pkg and postgres/src installations.

- Allow replicas to easily specify configuration overrides.

Bugfixes:

- (too many to mention)
