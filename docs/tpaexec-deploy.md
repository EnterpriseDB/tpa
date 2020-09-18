# tpaexec deploy

Deployment is the process of installing and configuring Postgres and
other software on the cluster's servers. This includes setting up
replication, backups, and so on.

At the end of the deployment stage, Postgres will be up and running
along with other components like repmgr, Barman, pgbouncer, etc.
(depending on the architecture selected).

## Prerequisites

Before you can run `tpaexec deploy`, you must have already run
[`tpaexec configure`](tpaexec-configure.md) to generate the cluster
configuration and then provisioned the servers with
[`tpaexec provision`](tpaexec-provision.md).

Before deployment, you must
`export TPA_2Q_SUBSCRIPTION_TOKEN=xxx` to enable any 2ndQuadrant
repositories that require subscription. You can use the subscription
token that you used to [install TPAexec](INSTALL.md) itself. If you
forget to do this, an error message will soon remind you.

## Quickstart

```bash
[tpa]$ tpaexec deploy ~/clusters/speedy -v
Using /opt/2ndQuadrant/TPA/ansible/ansible.cfg as config file

PLAY [Basic initialisation and fact discovery] ***************************************
...

PLAY [Set up TPA cluster nodes] ******************************************************
...

PLAY RECAP ***************************************************************************
zealot                     : ok=281  changed=116  unreachable=0    failed=0   
keeper                     : ok=284  changed=96   unreachable=0    failed=0   
quaver                     : ok=260  changed=89   unreachable=0    failed=0   
quavery                    : ok=260  changed=88   unreachable=0    failed=0   
quirk                      : ok=262  changed=100  unreachable=0    failed=0   


real    7m1.907s
user    3m2.492s
sys     1m5.318s
```

This command produces a great deal of output and may take a long time
(depending primarily on the latency between the host running tpaexec and
the hosts in the cluster, as well as how long it takes the instances to
download the packages they need to install). We recommend that you use
at least one `-v` during deployment. The output is also logged to
`ansible.log` in the cluster directory.

The exact number of hosts, tasks, and changed tasks may of course vary.

The deploy command takes no options itself—any options you provide after
the cluster name are passed on unmodified to Ansible (e.g., `-v`).

Those who are familiar with Ansible may be concerned by the occasional
red "failed" task output scrolling by. Rest assured that if the process
does not stop soon afterwards, the error is of no consequence, and the
code will recover from it automatically.

When the deployment is complete, you can run
[`tpaexec test`](tpaexec-test.md) to verify the installation.

## deploy.yml

The deployment process is architecture-specific. Here's an overview of
the various
[configuration settings that affect the deployment](configure-instance.md).
If you are familiar with Ansible playbooks, you can follow along as
tpaexec applies various roles to the cluster's instances.

Unlike config.yml, deploy.yml is not designed to be edited (and is
usually a link into the architectures directory). Even if you want to
extend the deployment process to run your own Ansible tasks, you should
do so by [creating hooks](tpaexec-hooks.md). This protects you from
future implementation changes within a particular architecture.
