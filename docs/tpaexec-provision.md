---
title: TPAexec configuration guide - provision
version: 1.5
date: 22/June/2018
author: Craig Alsop
copyright-holder: 2ndQuadrant Limited
copyright-years: 2014-2018
toc: true
---

tpaexec provision
=================

© Copyright 2ndQuadrant, 2014-2018. Confidential property of 2ndQuadrant; not for public release.

### TPAexec Overview


**TPAexec** is an orchestration tool that enables the repeatable and automated deployment of highly available PostgreSQL clusters that conform to TPA (Trusted PostgreSQL Architecture). It sets up a fully working database cluster with multiple nodes, replication and backup - all integrated and fully tested for both performance and high availability.

TPAexec setup works in Stages:

- Provisioning

- Deployment (includes Customization, Testing and Verification)

and can also be used for

- Rehydration (used for rapid deployment of patches or OS upgrades to AWS EC2 instances )

### Pre-requisites

You need an AWS access key id and secret access key for API access.[Read platforms/aws/README](https://github.com/2ndQuadrant/TPA/blob/master/platforms/aws/README.md) for details.

### TPA cluster configuration

To bring up a cluster with TPA, you will need to write two YAML files: config.yml describes the instances required; deploy.yml is a playbook that maps the desired roles to the provisioned instances. These files should be in a cluster-specific directory. Initial creation of these files should be accomplished by running the appropriate **tpaexec configure** command.
For the following example, we have called the new cluster **speedy**, and will create create config.yml & deploy.yml files in **~/tpa/clusters/speedy** using the following command:

```# tpaexec configure <path/clustername> --architecture <archname>
tpaexec configure ~/tpa/clusters/speedy --architecture M1 --platform aws --region eu-west-1 --subnet 10.33.180.0/24 --instance-type t2.micro --distribution Debian --minimal
```
*M1 refers to a Single Master architecture containing a single PG master, but may contain cascading replicas*

This will populate ~/tpa/clusters/speedy/config.yml with various parameters that can then be modified/added to.

You may optionally specify ``--postgres-version 10`` (the default) or any other major version of Postgres (e.g. 9.6). TPA supports Postgres 9.4 and above (9.4 and 9.5 are no longer actively maintained). By default, the latest version of every package is installed, however for support or compliance purposes, it may be necessary to select specific package versions. This can be done, for example, by using the options `--postgres-package-version`, `--repmgr-package-version`, `--barman-package-version`, ``--pgbouncer-package-version``, ``--pglogical-package-version``, and ``--bdr-package-version``.

```
--postgres-package-version 10.4-2.pgdg90+1
--repmgr-package-version 4.0.5-1.pgdg90+1
--barman-package-version 2.4-1.pgdg90+1
--pgbouncer-package-version '1.8*'
--pglogical-package-version '2.2.0*'
--bdr-package-version '3.0.2*'
```

The file config.yml has been split into logical sections for the purposes of description, and duplicate descriptions omitted from the tables where possible

#### Cluster definition

```
---
architecture: M1

cluster_name: speedy
cluster_tags:
  Owner: roadrunner
cluster_vars:
  vpn_network: 192.168.33.0/24
```

| Parameter:       | Description                                                  |
| :--------------- | ------------------------------------------------------------ |
| architecture:    | Sets architecture type (defaults to M1, which is Single Master) |
| cluster_name:    | This will be the name used to populate the AWS Security groups |
| cluster_tags:    | A hash of tag names and values follows this                  |
| Owner:           | This is used to populate the AWS "Owner" Tag Key (defaults to the user name running tpaexec) |
| cluster_vars:    | Used to set various cluster variables                        |
| vpn_network:     | Sets the VPN network                                         |

#### AWS EC2 parameters

This is a simple example with 2 subnets, 2 availability zones in one AWS region.

```
ec2_vpc:
  Name: Test
  
ec2_vpc_subnets:
  eu-west-1:
    10.33.29.0/28:
      az: eu-west-1a
    10.33.27.16/28:
      az: eu-west-1b
      
ec2_ami:
  Name: TPA-Debian-PGDG-10-2018*
  Owner: self     
```

| Parameter:       | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| ec2_vpc:         | Used to configure AWS EC2 virtual private cloud - look at [TPA/platforms/aws/provision.yml](https://github.com/2ndQuadrant/TPA/tree/master/platforms/aws/provision.yml). for more information |
| Name:            | Name of VPC - if this is set, then every region must have a VPC called this. VPC must already exist unless **cidr:** parameter is specified. |
| ec2_vpc_subnets: | Used to configure the VPC subnets                            |
| eu-west-1:       | AWS region                                                   |
| 10.33.29.0/28:   | Subnet a                                                     |
| az: eu-west-1a   | AWS Availability Zone                                        |
| 10.33.27.16/28:  | Subnet b                                                     |
| az: eu-west-1b   | AWS Availability Zone                                        |
| ec2_ami:         | Used for setting Amazon Machine Image information            |
| Name:            | AMI name (can include wildcard)                              |
| Owner:           | (Optional) If set to self, then specifies a private AMI      |

For more configuration details on AWS EC2 parameters, see  [AWS EC2 parameters - advanced](#aws-ec2-parameters---advanced)

#### Instance definitions

###### ***Node 1***

```
instance_defaults:
  vars:
    ansible_user: admin

instances:
  - node: 1
    Name: speedy-a
    type: t2.micro
    region: eu-west-1
    subnet: 10.33.14.0/24
    volumes:
        - raid_device: /dev/md0
          device_name: /dev/xvdb
          volume_type: gp2
          volume_size: 16
          raid_units: 2
          attach_existing: yes
          vars:
            volume_for: postgres_data
    role: primary
    vars:
      max_connections: 222
      shared_buffers: '64MB'
```
| Parameter:       | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| instance_defaults:| Used to specify default parameters for instances            |
| ansible_user:  | Admin user (Parameter ec2_ami_user is now deprecated)|
| instances:       | Used to specify parameters for each system                   |
| - node:          | **1** - Node number for this host. Used by Ansible to configure parameters for hosts. |
| Name:            | Hostname.                                                    |
| type:            | AMI type - changing this can have price and performance implications |
| region:          | AWS region for the host to be created in                     |
| subnet:          | Subnet for this host                                         |
| volumes:         | (Optional) OS specific parameters for creating volumes - in this case a gp2 32GB striped volume, mounted on the default PGDATA location /opt/postgres/data |
| role:            | **primary** - Used to define the server role (may be multiple) - in this case the db primary. Role names include: **primary, replica, barman, witness, log-server, openvpn-server, bdr, postgres-xl, coordinator, datanode, coordinator-replica, datanode-replica, gtm, gtm-standby, pgbouncer, postgres**. See [TPA/roles/platforms/common/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/platforms/common/tasks/main.yml) for more information. |
| vars:            | Used to override postgresql.conf variables. Note, these are actually set in **0001-tpa_restart.conf** (In Debian under /opt/postgres/data/conf.d/ ) |
| max_connections: | Maximum connections to database                              |
| shared_buffers:  | Memory dedicated to PostgreSQL to use for caching data       |

###### ***Node 2***

```
    - node: 2
      Name: speedy-b
      type: t2.micro
      region: eu-west-1
      subnet: 10.33.14.0/24
      volumes:
          - device_name: /dev/xvdb
            volume_type: gp2
            volume_size: 16
            attach_existing: yes
            vars:
              mountpoint: /var/lib/postgresql
      tags:
        role: replica
        upstream: speedy-a
        backup: speedy-d
```
| Parameter: | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| - node:    | **2** - Node number for this host. Used by Ansible to configure parameters for hosts. |
| volumes:   | (Optional) OS specific parameters for creating volumes - in this case a gp2 16GB volume, mounted on /var/lib/postgresql, the install directory for postgres. |
| tags:      | Used to specify tags for the server                          |
| role:      | **replica** - Used to define the server role - in this case it is a replica. If role is **replica**, then tag **upstream** needs to be defined. See [TPA/roles/platforms/common/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/platforms/common/tasks/main.yml) for more information. |
| upstream:  | (Optional) Hostname of server that is upstream from this one - **upstream: \<Name>** is used to connect  replicas to upstream servers. In this case speedy-a is replicating to speedy-b |
| backup:    | (Optional) Hostname of backup server                         |

###### ***Node 3***

```
   - node: 3
      Name: speedy-c
      type: t2.micro
      region: eu-west-1
      subnet: 10.33.21.0/24
      volumes:
          - device_name: /dev/xvdb
            volume_type: gp2
            volume_size: 16
            vars:
              volume_for: postgres_data
      tags:
        role: replica
        upstream: speedy-b
```
| Parameter: | Description                              |
| ---------- | ---------------------------------------- |
| - node:    | **3** - Node number for this host        |
| role:      | **replica** - Used to define the server role - in this case it is a replica. If role is **replica**, then tag **upstream** needs to be defined. See [TPA/roles/platforms/common/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/platforms/common/tasks/main.yml) for more information. |
| upstream:  | (Optional) Hostname of server that is upstream from this one - in this case speedy-b is replicating to speedy-c |

###### ***Node 4***

```
    - node: 4
      Name: speedy-d
      type: t2.micro
      region: eu-west-1
      subnet: 10.33.21.0/24
      volumes:
          - device_name: /dev/xvdb
            volume_type: gp2
            volume_size: 32
            vars:
              volume_for: postgres_data
      tags:
        role:
          - barman
          - witness
          - log-server
          - openvpn-server
        upstream: speedy-a
```
| Parameter:       | Description                              |
| ---------------- | ---------------------------------------- |
| - node:          | **4** - Node number for this host        |
| role:            | Used to define the server role (may be multiple). Role names include: **primary, replica, barman, witness, log-server, openvpn-server, bdr, postgres-xl, coordinator, datanode, coordinator-replica, datanode-replica, gtm, gtm-standby, pgbouncer, postgres**. See [TPA/roles/platforms/common/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/platforms/common/tasks/main.yml) for more information. |
| - barman         | Installs and configures Barman. See [TPA/roles/barman](https://github.com/2ndQuadrant/TPA/tree/master/roles/barman) for more information. |
| - witness        | Registers this node as a witness. See [TPA/roles/repmgr/witness/final/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/repmgr/witness/final/tasks/main.yml) for more information. |
| - log-server     | Defines this server as a log server, and makes every other server log to it. See [TPA/roles/platforms/common/tasks/main.yml](https://github.com/2ndQuadrant/TPA/tree/master/roles/platforms/common/tasks/main.yml) for more information. |
| - openvpn-server | Configures this node as an openvpn server. See [TPA/roles/sys/openvpn](https://github.com/2ndQuadrant/TPA/tree/master/roles/sys/openvpn) for more information. |
| upstream:        | (Optional) Hostname of server that is upstream from this one - in this case speedy-a is backing up to speedy-d |

We can now run **tpaexec provision ~/tpa/clusters/speedy** which will create the AWS hosts.

After this stage has completed, you should be able to connect to any of the provisioned hosts by ssh:

```
# Connect to host speedy-a using the auto generated key id_speedy
[~/tpa/clusters/speedy]$ ssh -F ssh_config -i id_speedy speedy-a
```

See [Appendix A](#appendix-a---using-existing-rsa-keys) for notes on how to re-use existing RSA keys for provisioning. 

*Before starting the deployment phase, it is suggested that you log out of any provisioned hosts, as login sessions can interfere with the mounting of additional volumes.*

------

### Volume parameters - advanced

In many installations, it is likely that there are existing company specific standards as to filesystem layouts - an example code snippet is shown below:

```
   volumes:
        - device_name: root
          volume_type: gp2
          volume_size: 16
        - device_name: /dev/xvdb
          volume_type: gp2
          volume_size: 24
          attach_existing: yes
          delete_on_termination: false
          vars:
            mountpoint: /var/lib/pgsql
        - device_name: /dev/xvdc
          volume_type: gp2
          volume_size: 100
          attach_existing: yes
          delete_on_termination: false
          vars:
            mountpoint: /var/lib/pgsql/tblspc_data01
        - raid_device: /dev/md0
          device_name: /dev/xvdd
          volume_type: gp2
          volume_size: 12
          raid_units: 2
          attach_existing: yes
          delete_on_termination: false
          vars:
            mountpoint: /var/lib/pgsql/tblspc_index01
    role: primary
    vars:
      postgres_data_dir: /var/lib/pgsql/tblspc_data01/data
```

This creates 4 different volumes:

- 16GB root volume mounted on /
- 24GB volume mounted on /var/lib/pgsql
- 100GB volume mounted on /var/lib/pgsql/tblspc_data01
- 24GB striped volume mounted on /var/lib/pgsql/tblspc_index01

The postgres data dir is set to /var/lib/pgsql/tblspc_data01/data

In this way it is possible to create extra volumes & associated mount points for each instance.

------

### AWS EC2 parameters - advanced

It is possible to use different VPCs in each region, e.g. specifying VPCs by id, this expanded form maps from region names to a VPC filter specification. If the VPC does not exist, and both Name, cidr are given ( *and* vpc-id is not in filters), it will be created.

###### Example - ec2_vpc with vpc-id specified

```
ec2_vpc:
  eu-west-1:
    Name: SpeedyVPC
    cidr: 192.0.2.0/24
    filters:
      vpc-id: vpc-abcdef
```

| Parameter: | Description                              |
| ---------- | ---------------------------------------- |
| eu-west-1: | AWS Region name                          |
| Name:      | VPC name                                 |
| cidr:      | CIDR                                     |
| filters:   | Allows us to specify the vpc-id          |
| vpc-id:    | Existing VPC id for this region to be used within this VPC (named by **Name:**) |

###### Example - ec2_vpc_subnets - complex

This block is from a more complicated config.

    ec2_ami:
      Name: ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20170803
    ec2_vpc:
      Name: Test
    
    ec2_vpc_subnets:
      eu-west-1:
        10.33.125.16/28:
          az: eu-west-1b
        10.33.125.32/28:
          az: eu-west-1c
        10.33.125.48/28:
          az: eu-west-1b
        10.33.125.64/28:
          az: eu-west-1c
      eu-central-1:
        10.33.125.80/28:
          az: eu-central-1a
        10.33.125.96/28:
          az: eu-central-1b
        10.33.125.112/28:
          az: eu-central-1a
        10.33.125.128/28:
          az: eu-central-1b
        10.33.125.144/28:
          az: eu-central-1b

In this we can see that 9 subnets have been set up - these are to allow one BDR master instance, two physical replicas, and a corresponding Barman instance in each of the local clusters on two regions, plus a control node.



------

# Appendix A - using existing RSA keys

By default, the **tpaexec provision** utility will create new RSA keys for ssh connection to the cluster hosts. If you want to reuse existing keys, then you can either 

1/ set the ssh_key_file variable in config.yml, giving it a relative path - for example with **id_speedy** and **id_speedy.pub** both sitting in the ~/tpa directory:

```
cluster_name: speedy
ssh_key_file: "../../id_speedy"
```

See [TPA/platforms/common/provision.yml](https://github.com/2ndQuadrant/TPA/platforms/common/provision.yml) for more information. 

2/ Alternatively, you can copy both public and private keys into the cluster directory (which contains config.yml and deploy.yml) before running tpaexec provision.

They will need to be named **id\_\<clustername>.pub** and **id\_\<clustername>** respectively - in this example they would be named id\_speedy.pub and id\_speedy.

[^Information Classification: Confidential]: [ISP008] Information Classification Policy


