---
title: TPAexec guide - rehydrate
version: 1.0
date: 01/June/2018
author: Craig Alsop
copyright-holder: 2ndQuadrant Limited
copyright-years: 2018
toc: true
---

TPAexec guide - rehydrate
==================

© Copyright 2ndQuadrant, 2018. Confidential property of 2ndQuadrant; not for public release.

### What is Rehydration?

Rehydration is a process that allows for rapid deployment of patches or OS upgrades to AWS EC2 instances managed by **TPAexec** orchestration tool. This is done by moving the storage volumes from existing EC2 instances provisioned from an old AMI, to new EC2 instances that have been provisioned from a new AMI that has been built with the latest patches.

The rehydration command requires the existing instance to be still present - i.e. don't terminate the instance via the AWS console. Logically rehydrate is nothing more than terminate followed by provision followed by deploy.

------

### Pre-requisites

To be able to use rehydration, 2 volume attributes need to be set in config.yml: 

- **delete_on_termination** needs to be set to "false", which will allow the volume to survive the termination of the instance it was attached to. (TPAexec sets this is set by default for gp2 volumes, but it is recommended that it is set explicitly to avoid confusion)
- **attach_existing** needs to be set to "yes", so that the volume will be searched for, and if found, will be passed to the instance in user-data which will run "aws ec2 attach-volume" commands to attach them after the new instance is started up. (Note - it is done like this, because AWS only allows attachment of existing volumes after the instance has already been started).

### Simple Rehydrate example

This example assumes that environment variable TPA_HOME has been set; that \$TPA_HOME/bin has been added to the tpauser's PATH. It also assumes that you have a running cluster called **night**, with the configuration files located in **\$TPA_HOME/clusters/night** and that the instance we want to rehydrate is called **zombie**.

Use the AWS console to check that all the instances in the cluster are running, and that all checks have passed, not just the instance(s) being hydrated, especially the master node - if they are in “stopped” or “terminated” state, TPAexec will build a new instance, which isn't what we want.



Before we can run **rehydrate night zombie** we first need to check and edit **config.yml**

Update the **ec2_ami** name with the AMI that you want the new instance to be built with (in this example we will be setting it to "TPA-Debian-PGDG-10-2018*" )

Check that **delete_on_termination** is already set false in the config.yml file. If the parameter isn't present, then you can check its setting via the Amazon EC2 management console. Click on ‘Instances’, select instance (in this case zombie), under the ‘Description’ tab, scroll down to ‘Block devices’, and click on the appropriate EBS volume. This will give a box which show the status of the Delete on Termination flag - if it is set to true, then it can be changed via aws command line (see [Appendix](#appendix) )

Check **attach_existing** in config.yml & set it to "yes" if it isn't set already.

#### config.yml fragment

```
ec2_ami:
  Name: TPA-Debian-PGDG-10-2018*
  Owner: self
ec2_ami_user: admin

instances:
    - node: 1
      Name: zombie
      type: t2.micro
      region: eu-west-1
      subnet: 10.33.14.0/24
      volumes:
            device_name: /dev/xvdb
            volume_type: gp2
            volume_size: 16
            raid_units: 2
            attach_existing: yes
            delete_on_termination: false
            vars:
              mountpoint: /var/lib/postgresql
```


### Command line:

**`$TPA_HOME/bin/rehydrate \<clusterdir> \<node1>[,node2[,node3]]... `**

```
<clusterdir>
	The directory containing the cluster config - if no path is given, it assumes that the directory will be under the "clusters" directory

<node1>
	There must be at least one node specified for the rehydrate command to execute

rehydrate will check whether delete_on_termination has been set to false for any relevant volumes, and if not set, will stop before any instance is terminated.

```

So, for our simple example:

```
[tpa]$ cd $TPA_HOME
[tpa]$ rehydrate night zombie
```

------

### More Complex Example:

A more realistic example needs to consider the cluster topology and co-ordinate node switchovers with any rehydration activity. So for a cluster (again named night) consisting of 9 nodes, with 5 nodes in East and 4 nodes in West:

- East
  - 1 Master (**vlad**)
  - 2 Replica (**zombie1, zombie2**)
  - 1 Barman+Standby Anchor pair (**igor, minion1**)
- West
  - 2 Replica (**zombie3, zombie4**)

  - 1 Barman+Standby Anchor pair (**fritz, minion2**)

#### Overview

Rehydration might consist of 3 logical phases:

##### Phase 1:

Rehydration is performed on a list of nodes that consists of:                                               
- 1 Barman Server plus its Standby Anchor located in same region as the current Master    
- ½ of Replica DB instances in each region

##### Phase 2:

Failover of current Master to instance in same region that has already been rehydrated
##### Phase 3:

Rehydration is performed on the list of remaining nodes.

------

#### Detail 

Edit $TPA_HOME/clusters/config.yml and change the ec2_ami Name to required AMI value

##### Phase 1:

Rehydrate nodes

```
[tpa]$ cd $TPA_HOME
[tpa]$ rehydrate night zombie1,zombie3,igor,minion1

```

Force a reregister as standby on each rehydrated Replica (only DB instances, not barman)

```
[tpa]$ ssh dba@zombie1
[dba]$ sudo su - postgres
[postgres]$ repmgr -f /etc/repmgr/<version>/repmgr.conf standby register -F

[tpa]$ ssh dba@zombie3
[dba]$ sudo su - postgres
[postgres]$ repmgr -f /etc/repmgr/<version>/repmgr.conf standby register -F
```

##### Phase 2:

Failover of current Master to instance in same region that has already been rehydrated: 

```
[tpa]$ ssh dba@zombie1
[dba]$ sudo su - postgres
[postgres]$ repmgr -f /etc/repmgr/<version>/repmgr.conf standby switchover —siblings-follow
```

You will see the below error message, however this is normal (When the switchover happens, the old master has to be restarted in order for it to connect to the new master as a standby)

```
ERROR: connection to database failed:
FATAL:  the database system is starting up
FATAL:  the database system is starting up

WARNING: switchover did not fully complete
DETAIL: node "zombie1" is now primary but node "vlad" is not reachable
```

##### Phase 3:

Rehydrate remaining nodes:

```
[tpa]$ cd $TPA_HOME
[tpa]$ rehydrate night vlad,zombie2,zombie4,fritz,minion2
```

Force a reregister as standby on each rehydrated Replica (only DB instances, not barman)

```
[tpa]$ ssh dba@zombie2
[dba]$ sudo su - postgres
[postgres]$ repmgr -f /etc/repmgr/<version>/repmgr.conf standby register -F

[tpa]$ ssh dba@zombie4
[dba]$ sudo su - postgres
[postgres]$ repmgr -f /etc/repmgr/<version>/repmgr.conf standby register -F
```



------

### Appendix
<a name="appendix"></a>

#### Using aws commandline to change volume attributes

You will need the Instance ID, region that the instance is in, as well as the block device name. (You can use AWS console to get Instance ID; region is just Availability Zone without the final letter).

example 1:

```
$ aws ec2 modify-instance-attribute --region eu-west-1 --instance-id i-0ca212ac1b0a5e7ff \
--block-device-mappings "[{\"DeviceName\": \"/dev/xvdb\",\"Ebs\":{\"DeleteOnTermination\":false}}]"
```

Check that this has worked  via the Amazon EC2 management console. Click on ‘Instances’, select instance (in this case zombie), under the ‘Description’ tab, scroll down to ‘Block devices’, and click on the appropriate EBS volume. This will give a box which show the status of the Delete on Termination flag, which should now be false. It is worth waiting for 30 seconds before running rehydrate, as it can take time to propagate the settings.

[^Information Classification: Confidential]: [ISP008] Information Classification Policy
