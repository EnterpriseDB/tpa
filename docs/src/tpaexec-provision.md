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
changed: [localhost] => (item=us-east-1:quirk)
changed: [localhost] => (item=us-east-1:keeper)
changed: [localhost] => (item=us-east-1:zealot)
changed: [localhost] => (item=us-east-1:quaver)
changed: [localhost] => (item=us-east-1:quavery)
...

TASK [Generate ssh_config file for the cluster] ***********************************
changed: [localhost]

PLAY RECAP ************************************************************************
localhost                  : ok=128  changed=20   unreachable=0    failed=0   


real    2m19.386s
user    0m51.819s
sys     0m27.852s
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
    UserKnownHostsFile "known_hosts tpa_known_hosts"
    ServerAliveInterval 60

Host quirk
    User admin
    HostName 54.227.207.189
Host keeper
    User admin
    HostName 34.229.111.196
Host zealot
    User admin
    HostName 18.207.108.211
Host quaver
    User admin
    HostName 54.236.36.251
Host quavery
    User admin
    HostName 34.200.214.150
[tpa]$ ssh -F ssh_config quirk
Linux quirk 4.9.0-6-amd64 #1 SMP Debian 4.9.82-1+deb9u3 (2018-03-02) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Sat Aug  4 12:31:28 2018 from 136.243.148.74
admin@quirk:~$ sudo -i
root@quirk:~# 
```

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
quirk ansible_host=54.227.207.189 node=1 platform=aws
keeper ansible_host=34.229.111.196 node=2 platform=aws
zealot ansible_host=18.207.108.211 node=3 platform=aws
quaver ansible_host=54.236.36.251 node=4 platform=aws
quavery ansible_host=34.200.214.150 node=5 platform=aws

[tpa]$ cat inventory/group_vars/tag_Cluster_speedy/01-speedy.yml 
cluster_name: speedy
cluster_tag: tag_Cluster_speedy
postgres_version: 15
tpa_version: v23.10-22-g30c1d5ea
tpa_2q_repositories: []
vpn_network: 192.168.33.0/24

[tpa]$ cat inventory/host_vars/zealot/02-topology.yml
role:
- barman
- log-server
- openvpn-server
- monitoring-server
- witness
upstream: quirk
```

If you now change a variable in config.yml and rerun provision, these
files will be updated. If you don't change the configuration, it won't
do anything. If you add a new instance in config.yml and rerun, it will
bring up the new instance without affecting the existing ones.
