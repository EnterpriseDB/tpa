tpaexec provision
=================

Provision creates instances and other resources required by the cluster.

The exact details of this process depend both on
the architecture (e.g., [M1](architectures/M1.md))
and platform (e.g., [AWS](platforms/aws.md))
that you selected while configuring the cluster.

At the end of the provisioning stage, you will have the required number
of instances with the basic operating system installed, which TPAexec
can access via ssh (with sudo to root).

## Prerequisites

Before you can provision a cluster, you must generate the cluster
configuration with [``tpaexec configure``](tpaexec-configure.md)
(and edit config.yml to fine-tune the configuration if needed).

You may need additional platform-dependent steps. For example, you need
to obtain an AWS API access keypair to provision EC2 instances, or set
up LXD or Docker to provision containers. Consult the platform
documentation for details.

## Quickstart

```
[tpa]$ tpaexec provision ~/clusters/speedy

PLAY [Provision cluster] **********************************************************************************************************************************************************************
…

TASK [Set up EC2 instances] *******************************************************************************************************************************************************************
changed: [localhost] => (item=us-east-1:quirk)
changed: [localhost] => (item=us-east-1:keeper)
changed: [localhost] => (item=us-east-1:zealot)
changed: [localhost] => (item=us-east-1:quaver)
changed: [localhost] => (item=us-east-1:quavery)
…

TASK [Generate ssh_config file for the cluster] ***********************************************************************************************************************************************
changed: [localhost]

PLAY RECAP ************************************************************************************************************************************************************************************
localhost                  : ok=128  changed=20   unreachable=0    failed=0   


real    5m19.386s
user    0m51.819s
sys     0m27.852s
```

This command will produce lots of output (append ``-v``, ``-vv``, etc.
to the command if you want even more verbose output).

If it completes without error, you may proceed to run
[``tpaexec deploy``](tpaexec-deploy.md) to install and configure
software.

## Options

When provisioning cloud instances, it is especially important to make
sure instances are directly traceable to a human responsible for them.
By default, TPAexec will tag EC2 instances as being owned by the login
name of the user running ``tpaexec provision``.

Specify ``--owner <name>`` to change the name (e.g., if your username
happens to be something generic, like postgres or ec2-user). You may use
initials, or "Firstname Lastname", or anything else to uniquely identify
a person.

Any other options you specify are passed on to ansible.

## Accessing the instances

After provisioning completes, you should be able to ssh to the instances
(after a brief delay to allow the instances to boot up and install their
ssh host keys). As shown in the output above, tpaexec will generate an
ssh_config file for you to use.

```
[tpa]$ cd ~/clusters/speedy
[tpa]$ cat ssh_config
Host *
    Port 22
    IdentitiesOnly yes
    IdentityFile "id_speedy"
    UserKnownHostsFile "known_hosts"
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
Linux ip-10-33-161-73 4.9.0-6-amd64 #1 SMP Debian 4.9.82-1+deb9u3 (2018-03-02) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Sat Aug  4 12:31:28 2018 from 136.243.148.74
admin@ip-10-33-161-73:~$ sudo -i
root@ip-10-33-161-73:~# 
```

Note that the host is named "quirk" in config.yml and ssh_config, but
its hostname is not set to quirk yet. This will happen during the
deployment phase.

You can run ``tpaexec deploy`` immediately after provisioning. It will
wait as long as required for the instances to come up. You do not need
to wait for the instances to come up, or ssh in to them before you
start deployment.
