---
title: TPAexec configuration guide - provision - baremetal
version: 1.1
date: 20/June/2018
author: Craig Alsop
copyright-holder: 2ndQuadrant Limited
copyright-years: 2014-2018
toc: true
---

TPAexec configuration guide - provision - baremetal
==================

© Copyright 2ndQuadrant, 2014-2018. Confidential property of 2ndQuadrant; not for public release.

### TPAexec Overview


**TPAexec** is an orchestration tool that enables the repeatable and automated deployment of highly available PostgreSQL clusters that conform to TPA (Trusted PostgreSQL Architecture). It sets up a fully working database cluster with multiple nodes, replication and backup - all integrated and fully tested for both performance and high availability. It can be used for different platforms, and this document looks at how to deploy to existing "baremetal" server instances.

TPAexec setup works in Stages:

- Provisioning

- Deployment (includes Customization, Testing and Verification)

### OS cluster
For baremetal deployment, we assume that the servers/VMs have already been created and booted to the OS, and that they are accessible via SSH.

**Pre-requisites that you will need:**

- Hostname and external ip address of each server (Name, public_ip)

- Private IP address of each server if different from public (private_ip)
- Cluster network CIDR (cluster_network)
- Cluster ssh user - the ssh user to administer cluster commands (cluster_ssh_user)
- Ansible ssh user - the admin user used to ssh to each host by tpaexec (ansible_user)
- If using repmgr, you will need to know logically which data centre hosts are in.

**Creating OS cluster using Vagrant with VirtualBox**

One method of quickly creating VMs for testing purposes is with [Vagrant](https://www.vagrantup.com/),which is becoming increasingly popular for managing VMs - an example Vagrantfile which creates 3 Centos servers which can be used by the TPA example below can be found in **Appendix 2** of this document.

Assuming that you have copied the **Vagrantfile** into a new vagrant project directory, and are using the tpa user to run vagrant, you should be able to run:

```
[tpa]$ cd <vagrant project>
[tpa]$ vagrant up
```
In the example, we are using an existing ssh key pair which live in ~/tpa/sshkeys/
```
[tpa]$ ls ~/tpa/sshkeys
id_night  id_night.pub
```
Vagrant will create a user `admin`, then copy the public key to `/home/admin/.ssh/authorized_keys` on each VM so that this user and key can be used by TPA to deploy the cluster.

### TPA cluster configuration

There is an example configuration located under in **Appendix 1** of this document. It is suggested that this is copied and used as a starting point. For the following example, we have called the new cluster **baretest**, and copied the files to **~/tpa/clusters/baretest**. 

### Provisioning

For the baremetal platform, **tpaexec provision \<clustername>** tries to populate the cluster directory with appropriate configuration files needed for the deployment phase. Before we can run **tpaexec provision ~/tpa/clusters/baretest** we first need to edit **config.yml** to make sure it has enough to work with.

The file config.yml has been split into logical sections for the purposes of description, and duplicate descriptions omitted from the tables where possible

#### Cluster definition

```
---

cluster_name: baretest
ssh_key_file: "../../sshkeys/id_night"
cluster_vars:
  cluster_network: 192.168.0.0/16
  cluster_ssh_user: admin
```
| Parameter:       | Description                              |
| :--------------- | ---------------------------------------- |
| cluster_name:    | Name of the cluster |
| ssh_key_file:    | Used to supply ssh keys to the cluster - expects 2 keys - <id_file> and <id_file.pub>    |
| cluster_vars:    | Used to set various cluster variables    |
| cluster_network: | Sets the cluster network                 |
| cluster_ssh_user: | Sets the cluster ssh user               |

By default, the tpaexec provision utility will create new RSA keys for ssh connection to the cluster hosts. Here we are reusing existing keys, so we have set the ssh_key_file variable in config.yml, giving it a relative path - for example with **id_night** and **id_night.pub** both sitting in the ~tpa/sshkeys directory:

#### Instance  definitions

```
---

instance_defaults:
  platform: bare

instances:
    - node: 1
      Name: lab-primary
      public_ip: 192.168.56.101
      tags:
        role:
          - primary
        backup: lab-backup
      vars:
        ansible_user: admin
        repmgr_location: dc1
        work_mem: 20MB
        max_connections: 234
        shared_buffers: 128MB

```

| Parameter:       | Description                              |
| :--------------- | ---------------------------------------- |
|instance_defaults: | Used for setting up defaults|
|platform: | Set default platform to bare|
| node: | Node id               |
| Name: | hostname for the node               |
| public_ip: | Sets the public IP address for a node          |
| private_ip: | Sets the private IP address for a node          |
| vars: | Mostly used to override postgresql.conf variables. Note, these are actually set in **0001-tpa_restart.conf** (In Debian under /opt/postgres/data/conf.d/ )|
| ansible_user: | Admin user used to connect to host          |
| repmgr_location: | Arbitrary string used to denote data centre host is in, so that failover decisions can be made.          |
| work_mem: | Memory to be used by internal sorts and hashes  |
| max_connections: | Maximum connections to database          |
| shared_buffers: | Memory dedicated to PostgreSQL to use for caching data          |

We can now run run tpaexec provision ~/tpa/clusters/baretest. If you are using an existing ssh key pair,  you should update ~/tpa/clusters/baretest/known_hosts, so that the deploy phase can access each host. Note - ssh-keyscan requires all the hosts to be contactable.
```
[tpa]$ tpaexec provision ~/tpa/clusters/baretest
[tpa]$ ssh-keyscan 192.168.56.101 > ~/tpa/clusters/baretest/known_hosts
[tpa]$ ssh-keyscan 192.168.56.102 >> ~/tpa/clusters/baretest/known_hosts 
[tpa]$ ssh-keyscan 192.168.56.103 >> ~/tpa/clusters/baretest/known_hosts 
```
We can now run tpaexec deploy ~/tpa/clusters/baretest.  (See TPAexec-Deploy.md for more information).

------

### Appendix 1 - config.yml file

```
---

cluster_name: bare
ssh_key_file: "../../sshkeys/id_night"
cluster_vars:
  cluster_network: 192.168.0.0/16
  cluster_ssh_user: admin

instance_defaults:
  platform: bare
instances:
    - node: 1
      Name: lab-primary
      public_ip: 192.168.56.101
#      private_ip: 10.33.243.230
      tags:
        role:
          - primary
        backup: lab-backup
      vars:
        ansible_user: admin
        repmgr_location: dc1
        work_mem: 20MB
        max_connections: 234
        shared_buffers: 128MB
    - node: 2
      Name: lab-backup
      public_ip: 192.168.56.103
#      private_ip: 10.33.243.86
      tags:
        role:
          - barman
          - witness
          - log-server
        upstream: lab-primary
      vars:
        ansible_user: admin
        repmgr_location: dc1
    - node: 3
      Name: lab-replica
      public_ip: 192.168.56.102
#      private_ip: 10.33.243.17
      tags:
        role:
          - replica
        upstream: lab-primary
      vars:
        ansible_user: admin
        repmgr_location: dc1
        work_mem: 21MB
        postgres_data_dir: /var/lib/postgresql/data
```
------

### Appendix 2 - Vagrant config - Vagrantfile

```
$script = <<SCRIPT
sudo yum -y install net-tools
## add admin
sudo useradd -m -s /bin/bash -U admin -u 666 --groups wheel
sudo mv /tmp/.ssh /home/admin
sudo chown -R admin:admin /home/admin
sudo chmod 700 /home/admin/.ssh
sudo chmod 600 /home/admin/.ssh/authorized_keys
sudo echo "%admin ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/admin
SCRIPT
Vagrant.configure("2") do |config|
  config.vm.box = "centos/7"
  config.vm.provision "file", source: "~/tpa/sshkeys/id_night.pub", destination: "/tmp/.ssh/authorized_keys"
  config.vm.provision "shell", inline: $script
  config.vm.define "primary" do |primary|
    primary.vm.hostname = 'lab-primary'
    primary.vm.network :private_network, ip: "192.168.56.101"
    primary.vm.network :forwarded_port, guest: 22, host: 10122, id: "ssh"
    primary.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
#      v.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
      v.customize ["modifyvm", :id, "--memory", 512]
      v.customize ["modifyvm", :id, "--name", "lab-primary"]
    end
  end
  config.vm.define "replica" do |replica|
    replica.vm.hostname = 'lab-replica'
    replica.vm.network :private_network, ip: "192.168.56.102"
    replica.vm.network :forwarded_port, guest: 22, host: 10222, id: "ssh"
    replica.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
#      v.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
      v.customize ["modifyvm", :id, "--memory", 512]
      v.customize ["modifyvm", :id, "--name", "lab-replica"]
    end
  end
  config.vm.define "backup" do |backup|
    backup.vm.hostname = 'lab-backup'
    backup.vm.network :private_network, ip: "192.168.56.103"
    backup.vm.network :forwarded_port, guest: 22, host: 10322, id: "ssh"
    backup.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
#      v.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
      v.customize ["modifyvm", :id, "--memory", 512]
      v.customize ["modifyvm", :id, "--name", "lab-backup"]
    end
  end
end
```
In this multi host example, we are creating 3 VMs - lab-primary, lab-backup & lab-replica, using an existing ssh key pair which live in ~/tpa/sshkeys/
```
[tpa]$ ls ~/tpa/sshkeys
id_night  id_night.pub
```
Vagrant will first copy the public key to /tmp, then via a script, create a user `admin` copy the public key to `/home/admin/.ssh/authorized_keys` and set permissions on each VM so that this user and key can be used by TPA to deploy the cluster.
The VirtualBox forwarded SSH ports have been set to 10122, 10222 & 10322 respectively.

[^Information Classification: Confidential]: [ISP008] Information Classification Policy

