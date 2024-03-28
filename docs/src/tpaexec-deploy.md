# tpaexec deploy

Deployment is the process of installing and configuring Postgres and
other software on the cluster's servers. This process includes setting up
replication, backups, and so on.

At the end of the deployment stage, Postgres will be up and running
along with other components like repmgr, Barman, pgbouncer, and so on,
depending on the architecture selected.

## Prerequisites

Before you can run `tpaexec deploy`, you must run
[`tpaexec configure`](tpaexec-configure.md) to generate the cluster
configuration. You then must provision the servers with
[`tpaexec provision`](tpaexec-provision.md).

Before deployment, you must run
`export TPA_2Q_SUBSCRIPTION_TOKEN=xxx` to enable any 2ndQuadrant
repositories that require a subscription. You can use the subscription
token that you used to [install TPA](INSTALL.md). If you
forget to do this, an error message reminds you.

## Quick start

```bash
[tpa]$ tpaexec deploy ~/clusters/speedy -v
Using /opt/EDB/TPA/ansible/ansible.cfg as config file

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

This command produces a lot of output and can take a long time.
The time it takes depends primarily on the latency between the host running tpaexec and
the hosts in the cluster. It also depends on how long it takes the instances to
download the packages they need to install. We recommend that you use
at least one `-v` during deployment. The output is also logged to
`ansible.log` in the cluster directory.

The exact number of hosts, tasks, and changed tasks varies based on your needs.

The `deploy` command takes no options. Any options you provide after
the cluster name are passed on, unmodified, to Ansible (for example, `-v`).

If you're familiar with Ansible, you might be concerned to see the occasional
red "failed" task output scrolling by. However, if the process
doesn't stop soon after, the error has no effect, and the
code recovers from it without the need for action.

When the deployment is complete, you can run
[`tpaexec test`](tpaexec-test.md) to verify the installation.

## Selective deployment

You can limit the deployment to a subset of your hosts by setting
`deploy_hosts` to a comma-separated list of instance names:

```bash
[tpa]$ tpaexec deploy ~/clusters/speedy -v -e deploy_hosts=keeper,quaver
```

This command runs the deployment on the given instances, but it also
initially executes some tasks on other hosts to collect information about
the state of the cluster.

!!! Note
    We recommend setting `deploy_hosts` instead of using
    Ansible's `--limit` option, which TPA doesn't support.

## deploy.yml

The deployment process is architecture specific. See this overview of
the various
[configuration settings that affect the deployment](configure-instance.md).
If you're familiar with Ansible playbooks, you can follow along as
tpaexec applies various roles to the cluster's instances.

Unlike `config.yml`, `deploy.yml` isn't designed to be edited. It's
usually a link into the architectures directory. Even if you want to
extend the deployment process to run your own Ansible tasks,
do so by [creating hooks](tpaexec-hooks.md). This technique protects you from
future implementation changes in a particular architecture.
