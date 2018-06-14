---
title: TPA configuration guide - deploy
version: 1.3
date: 14/June/2018
author: Craig Alsop
copyright-holder: 2ndQuadrant Limited
copyright-years: 2014-2018
toc: true
---

TPA configuration guide - deploy
==================

© Copyright 2ndQuadrant, 2018. Confidential property of 2ndQuadrant; not for public release.

### Overview


This guide is designed to follow on from the TPA configuration guide - provision, and covers the deployment stage, which is the part that sets up a fully working database cluster with multiple nodes, replication and backup - all integrated and fully tested for both performance and high availability.

### Pre-requisite

You will need to have run the provision stage first ( **tpaexec provision \<clustername>** )  - see [TPAexec configuration guide - provision](https://github.com/2ndQuadrant/TPA/tree/master/docs/TPAexec-provision.md).

If you are not using a private repo for the deployment packages, you will need to specify a repo password for the relevant 2ndQuadrant repo [RHEL/Centos rpms](https://rpm-internal.2ndquadrant.com/site/content/) or [Debian/Ubunto deb packages](https://apt-internal.2ndquadrant.com/site/content/)
   ```
   export TPA_2Q_REPO_PASSWORD=putPASSWORDhere
   ```


### TPA cluster Deployment

In this document, we are continuing where [TPAexec configuration guide - provision](https://github.com/2ndQuadrant/TPA/blob/master/docs/TPAexec-provision.md) left off, and assuming that we have provisioned a new cluster **speedy**, with TPA config files in **~/tpa/clusters/test/speedy**. 

```
	$ ls ~/tpa/clusters/test/speedy
	certs       hostkeys       inventory    ssh_config  vault
	config.yml  id_speedy      keys         tmp
	deploy.yml  id_speedy.pub  known_hosts  vars.json
```

Looking in the inventory directory, we can see that a file called **00-speedy** has been created, containing the hostname information - this can be used to cross-check the information being used to build the servers.

```
	$ cat ~/tpa/clusters/speedy/inventory/00-speedy
	[tag_Cluster_speedy]
	speedy-a ansible_host=34.240.16.222 node=1
	speedy-b ansible_host=54.154.64.43 node=2
	speedy-c ansible_host=54.229.220.113 node=3
	speedy-d ansible_host=54.229.136.91 node=4
```



Before we can run **tpaexec deploy ~/tpa/clusters/speedy** we first need to edit **deploy.yml**

The file deploy.yml has been split into logical sections for the purposes of description

### Basic initialisation and fact discovery

```
---

# This play must always be applied to all hosts in the cluster. Here we
# do any platform-specific checks and initialisation, confirm that all
# hosts are available, and perform basic fast discovery.

- name: Basic initialisation and fact discovery
  any_errors_fatal: True
  max_fail_percentage: 0

  hosts: all
  roles:
    - role: platforms
      tags: always

    - role: facts
      tags: always

    - role: postgres/vars
      vars:
        postgres_version: 10
      tags: always

```

| Parameter:           | Description                                                  |
| :------------------- | ------------------------------------------------------------ |
| - name:              | Name of this ansible play                                    |
| any_errors_fatal:    | This should be left set to "True", as we need to confirm that all hosts are reachable |
| max_fail_percentage: | This should be left set to "0"                               |
| hosts:               | The hosts that this play will target - leave set to "all"    |
| roles:               | Used to set which roles to be applied to hosts               |
| - role:              | **platforms** - Sets up platform specific checks and initialisation, by applying the roles defined in [TPA/roles/platforms](https://github.com/2ndQuadrant/TPA/tree/master/roles/platforms). |
| tags:                | **always** - always apply the associated role                |
| - role:              | **facts** - Performs "lightweight" distribution detection, by applying the roles defined in [TPA/roles/facts](https://github.com/2ndQuadrant/TPA/tree/master/roles/facts), to see what OS is being deployed to. Supports Debian, RedHat, and Ubuntu. |
| tags:                | **always** - always apply the associated role                |
| - role:              | **postgres/vars** - Sets up the PostgreSQL version, by applying the roles defined in [TPA/roles/postgres/vars](https://github.com/2ndQuadrant/TPA/tree/master/roles/postgres/vars). |
| vars:                | Variables to be applied                                      |
| postgres_version:    | **10** - The PostgreSQL version to be deployed               |
| tags:                | **always** - always apply the associated role                |

### Install Postgres

```
# Now the cluster hosts are reachable by ssh and have all the required
# inventory variables set. We can get on with installing Postgres.

- name: Set up TPA cluster nodes
  any_errors_fatal: True
  max_fail_percentage: 0
  sudo_user: root
  sudo: true

  hosts: "{{ deploy_hosts|default('all') }}"
  roles:
    - role: common

    # Set up any additional filesystems required. The block device
    # layout is instance-specific.
    - role: sys/fs
      vars:
        device: "{{ volumes[0].device }}"
        mountpoint: "{{ postgres_home }}"
      tags: [sys, fs]

    # Computes memory size and other instance-specific computations for
    # use in later steps (e.g., setting shared_buffers).
    - role: sys/tune
      tags: always

    - role: sys/sysctl
      vars:
        sysctl_values:
          net.ipv4.ip_forward: 1
      tags: [sys, sysctl]

    - role: sys/sysstat
      tags: [sys, sysstat]

    - role: sys/openvpn
      when: >
        'tag_role_openvpn-server' in groups
        and vpn_network is defined

    - role: sys/hosts
      tags: [sys, hosts]

    - role: sys/rsyslog
      tags: [sys, rsyslog]

    - role: postgres
      when: >
        'postgres' in role

    - role: barman
      tags: barman

    - role: repmgr
      tags: repmgr

    - role: postgres/final
      when: >
        'postgres' in role
      tags: [postgres, final]

    - role: monitoring
      when: >
        'tag_role_monitoring-server' in groups
      tags: monitoring
```

| Parameter:           | Description                                                  |
| :------------------- | ------------------------------------------------------------ |
| - name:              | Name of this ansible play                                    |
| any_errors_fatal:    | This should be left set to "True", as we need to confirm that all hosts are reachable |
| max_fail_percentage: | This should be left set to "0"                               |
| sudo_user:           | Set to the user to run sudo commands as.                     |
| sudo:                | **true** - Used to set whether sudo is to be used.           |
| hosts:               | **"{{ deploy_hosts\|default('all') }}"** - Defines which hosts will be deployed to. For the \$TPA_DIR/bin/**deploy** script, this will default to all; when deploy.yml  is used by the \$TPA_DIR/bin/**rehydrate** script, it will define the individual hosts to be rehydrated. See [TPAexec guide - rehydrate](https://github.com/2ndQuadrant/TPA/blob/master/docs/TPAexec-rehydrate.md) for more info. |
| roles:               | Sets up all the deployment roles                             |
| - role:              | **common** - Applied to all hosts                            |
| - role:              | **sys/fs** - Sets up the filesystems. See [TPA/roles/sys/fs/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/sys/fs/tasks/main.yml) for more info. |
| - role:              | **sys/tune** - Role for calculating the system tuning parameters. Computes memory size and other instance-specific computations. See [TPA/roles/sys/fs/tune/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/sys/fs/tune/main.yml) for more info. |
| - role:              | **sys/sysctl** - Role for setting up sysctl values to be merged with the defaults - see [TPA/roles/sys/sysctl/defaults/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/sys/sysctl/defaults/main.yml) for more info. |
| - role:              | **sys/sysstat** - Configures and enables systat - see [TPA/roles/sys/sysstat/tasks/os](https://github.com/2ndQuadrant/TPA/tree/master/roles/sys/sysstat/tasks/os) for Debian and RHEL info. |
| - role:              | **sys/openvpn** - Configures and enables openvpn - see **sys/sysstat** - Configures and enables systat - see [TPA/roles/sys/openvpn/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/sys/openvpn/tasks/main.yml) for more info. |
| - role:              | **sys/hosts** - Generates the /etc/hosts and /etc/ssh/ssh_known_hosts files. See  [TPA/roles/sys/hosts/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/sys/hosts/tasks/main.yml) for more info. |
| - role:              | **sys/rsyslog** - Create rsyslog.conf config file & ensure rsyslog service is enabled on boot. See [TPA/roles/sys/rsyslog/server/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/sys/rsyslog/server/tasks/main.yml) for more info. |
| - role:              | **postgres** - Configures postgres on every postgres instance with a valid PGDATA. Creates **pg_hba.conf** & **postgresql.conf** in PGDATA, and tries to create 0000-tpa.conf, 0001-tpa_restart.conf, 1111-extensions.conf, 8888-{{ variable_name }}*.conf, 9900-role-settings.conf, 9999-override.conf in **PGDATA/conf.d**. [TPA/roles/postgres/config/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/postgres/config/tasks/main.yml) is recommended reading. |
| - role:              | **barman** - Installs, configures & enable Barman on any server where tags.role includes 'barman'. On instances to be backed up (i.e., with tags.backup set to the name of a Barman server) it will perform client-side configuration. See [TPA/roles/barman/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/barman/tasks/main.yml) for more info. |
| - role:              | **repmgr**- Install, config & enable the repmgr service. See [TPA/roles/repmgr/service/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/repmgr/service/tasks/main.yml) for more info. |
| - role:              | **postgres/final** - Force immediate backup for any instances that do not have any backups at all. See [TPA/roles/postgres/final/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/postgres/final/tasks/main.yml) for more info. |
| - role:              | **monitoring** - Sets up monitoring; installs and configures icinga & NSCA-ng. See [TPA/roles/monitoring/server/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/monitoring/server/tasks/main.yml) for more info. |

### Cleanup /etc/hosts

This code block is there to ensure that a re-deployment works even when limited to a subset of hosts

```
# Finally, we must make sure we don't leave stale entries in /etc/hosts
# anywhere. (This won't matter for an initial deployment, because the
# role has already been applied above, but it will matter if we run a
# re-deployment limited to certain hosts.)

- name: Ensure /etc/hosts is correct cluster-wide
  any_errors_fatal: True
  max_fail_percentage: 0
  sudo_user: root
  sudo: yes
  hosts: all
  roles:
    - role: sys/hosts
      tags: [sys, hosts]
```

| Parameter:           | Description                              |
| -------------------- | ---------------------------------------- |
| - name:              | Name of this ansible play.               |
| any_errors_fatal:    | This should be left set to **True**      |
| max_fail_percentage: | This should be left set as **0**         |
| sudo_user:           | **root** - Set to the user to run sudo commands as. |
| sudo:                | **yes** - Used to set whether sudo is to be used. |
| hosts:               | **all** - which hosts to apply the following roles to. |
| roles:               | Roles to be applied                      |
| - role:              | **sys/hosts** - Generates the /etc/hosts and /etc/ssh/ssh_known_hosts files. See  [TPA/roles/sys/hosts/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/sys/hosts/tasks/main.yml) for more info. |

### Deploy

Run **tpaexec deploy ~/tpa/clusters/speedy**

(Note, the previous method of running **$TPA_DIR/bin/deploy ~/tpa/clusters/speedy** will still work)



[^Information Classification: Confidential]: [ISP008] Information Classification Policy

