tpaexec switchover
=================

The ``tpaexec switchover`` command promotes a DB standby to be the primary in the cluster, and can be used in place of the `repmgr standby switchover --siblings-follow` command.
It performs various repmgr sanity checks before switching over the node, and is designed to be run from the tpaexec server without having to shut down any repmgr services beforehand.

**`tpaexec switchover <clustername> <standby-nodename>`** can be used to promote a standby to become the master, and any standbys attached to the old primary will be configured to follow the new primary.

### Prerequisites

This command relies on the relevant achitecture commands directory containing commands linked from the cluster directory created as standard if `tpaexec configure` is used. If the links are not present, they will need to be linked manually e.g. if you are using an existing cluster directory. For example, for a Single Master (M1) architecture, with tpaexec installed in the default directory:

```
[tpa]$ cd <clusterdir>
[tpa]$ mkdir commands
[tpa]$ cd commands
[tpa]$ ln -s /opt/2ndQuadrant/TPA/architectures/M1/commands/switchover.sh switchover.sh
[tpa]$ ln -s /opt/2ndQuadrant/TPA/architectures/M1/commands/switchover.yml switchover.yml
[tpa]$ ln -s /opt/2ndQuadrant/TPA/architectures/M1/commands/update-postgres.yml \
update-postgres.yml
```

### Architecture options

At the moment this command is only relevant to the M1 architecture, and should not be attempted for any other architecture.

