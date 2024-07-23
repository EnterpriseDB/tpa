---
description: The command to provision instances and resources for a TPA cluster.
---

# tpaexec provision

Provision creates instances and other resources required by the cluster.

The exact details of this process depend both on
the architecture (e.g. [M1](architecture-M1.md))
and platform (e.g. [AWS](platform-aws.md))
that you selected while configuring the cluster.

At the end of the provisioning stage, you will have the required number
of instances with the basic operating system installed, which TPA
can access via ssh (with sudo to root).

## Prerequisites

Before you can provision a cluster, you must generate the cluster
configuration with [`tpaexec configure`](tpaexec-configure.md)
(and edit config.yml to fine-tune the configuration if needed).

You may need additional platform-dependent steps. For example, you need
to obtain an AWS API access keypair to provision EC2 instances, or set
up LXD or Docker to provision containers. Consult the platform
documentation for details.

## Quickstart

```bash
[tpa]$ tpaexec provision ~/clusters/speedy

PLAY [Provision cluster] **********************************************************
...

TASK [Set up EC2 instances] *******************************************************
changed: [localhost] => (item=us-east-1:uproar)
changed: [localhost] => (item=us-east-1:unravel)
changed: [localhost] => (item=us-east-1:kinsman)
...

TASK [Generate ssh_config file for the cluster] ***********************************
changed: [localhost]

PLAY RECAP ************************************************************************
localhost                  : ok=163  changed=35   unreachable=0    failed=0    skipped=44   rescued=0    ignored=2


real	4m42.726s
user	0m39.101s
sys	    0m15.687s
```

This command will produce lots of output (append `-v`, `-vv`, etc.
to the command if you want even more verbose output). The output is also
logged to `ansible.log` in the cluster directory. This can be overriden
by setting the environment variable `ANSIBLE_LOG_PATH` to the path and name of
the desired logfile.

If it completes without error, you may proceed to run
[`tpaexec deploy`](tpaexec-deploy.md) to install and configure
software.

## Options

When provisioning cloud instances, it is especially important to make
sure instances are directly traceable to a human responsible for them.
By default, TPA will tag EC2 instances as being owned by the login
name of the user running `tpaexec provision`.

Specify `--owner <name>` to change the name (e.g., if your username
happens to be something generic, like postgres or ec2-user). You may use
initials, or "Firstname Lastname", or anything else to uniquely identify
a person.

Any other options you specify are passed on to Ansible.

## Accessing the instances

After provisioning completes, you should be able to SSH to the instances
(after a brief delay to allow the instances to boot up and install their
SSH host keys). As shown in the output above, tpaexec will generate an
ssh_config file for you to use.

```bash
[tpa]$ cd ~/clusters/speedy
[tpa]$ cat ssh_config
Host *
    Port 22
    IdentitiesOnly yes
    IdentityFile "id_speedy"
    UserKnownHostsFile known_hosts tpa_known_hosts
    ServerAliveInterval 60

Host uproar
    User admin
    HostName 3.88.255.205
Host unravel
    User admin
    HostName 54.80.99.142
Host kinsman
    User admin
    HostName 54.165.229.179
```

To login to a host, use the command `ssh -F ssh_config` followed by the
hostname. For example `ssh -F ssh_config uproar`.

You can run [`tpaexec deploy`](tpaexec-deploy.md) immediately after
provisioning. It will wait as long as required for the instances to come
up. You do not need to wait for the instances to come up, or ssh in to
them before you start deployment.

## Generated files

During the provisioning process, a number of new files will be created
in the cluster directory:

```bash
[tpa]$ ls ~/clusters/speedy
total 240
-rw-r--r-- 1 ams ams 193098 Aug  4 17:59 ansible.log
drwxr-xr-x 2 ams ams   4096 Aug  4 17:38 commands
-rw-r--r-- 1 ams ams   1442 Aug  4 17:54 config.yml
lrwxrwxrwx 1 ams ams     51 Aug  4 17:38 deploy.yml -> 
                             /opt/EDB/TPA/architectures/M1/deploy.yml
drwxr-xr-x 2 ams ams   4096 Aug  4 17:38 hostkeys
-rw------- 1 ams ams   1675 Aug  4 17:38 id_speedy
-rw------- 1 ams ams   1438 Aug  4 17:38 id_speedy.ppk
-rw-r--r-- 1 ams ams    393 Aug  4 17:38 id_speedy.pub
drwxr-xr-x 4 ams ams   4096 Aug  4 17:50 inventory
-rw-r--r-- 1 ams ams   2928 Aug  4 17:50 tpa_known_hosts
-rw-r--r-- 1 ams ams    410 Aug  4 17:50 ssh_config
-rw-r--r-- 1 ams ams   3395 Aug  4 17:59 vars.json
drwxr-xr-x 2 ams ams   4096 Aug  4 17:38 vault
```

We've already studied the ssh_config file, which refers to the `id_*`
files (an SSH keypair generated for the cluster) and `tpa_known_hosts`
(the signatures of the `hostkeys/` installed on the instances).

The `vars.json` file may be used by `tpaexec provision` on
subsequent invocations with `--cached`.

The `inventory/` directory contains static and dynamic inventory files
as well as group and host variable definitions from config.yml.

```bash
[tpa]$ cat inventory/00-speedy
[tag_Cluster_speedy]
uproar ansible_host=3.88.255.205 node=1 platform=aws
unravel ansible_host=54.80.99.142 node=2 platform=aws
kinsman ansible_host=54.165.229.179 node=3 platform=aws

[tpa]$ cat inventory/group_vars/tag_Cluster_speedy/01-speedy.yml 
cluster_name: speedy
cluster_tag: tag_Cluster_speedy
edb_repositories: []
failover_manager: repmgr
keyring_backend: system
postgres_flavour: postgresql
postgres_version: '14'
preferred_python_version: python3
ssh_key_file: id_speedy
tpa_version: v23.33-24-g4c0909d1
use_volatile_subscriptions: false

[tpa]$ cat inventory/host_vars/kinsman/01-instance_vars.yml
ansible_user: admin
location: main
region: us-east-1
role:
- barman
- log-server
- witness
upstream: uproar
volumes:
- device: /dev/xvda
- device: /dev/sdf
  volume_for: barman_data
```

If you now change a variable in config.yml and rerun provision, these
files will be updated. If you don't change the configuration, it won't
do anything. If you add a new instance in config.yml and rerun, it will
bring up the new instance without affecting the existing ones.
