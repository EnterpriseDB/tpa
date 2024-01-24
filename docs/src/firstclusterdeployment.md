# A first cluster deployment

In this short tutorial, you work through deploying a simple [M1 architecture](architecture-M1.md) deployment onto a local Docker installation. By the end of the tutorial, you will have four containers, one primary database, two replicas, and a backup node configured and ready for you to explore.

This example runs TPA on an Ubuntu system, but the considerations are similar for most Linux systems.

### Installing TPA

If you're an EDB customer, first follow the [EDB repo instructions](INSTALL.md), which install the TPA packages straight from EDB's repositories.

If you're an open source user of TPA, first see the [instructions on how to build from the source](INSTALL-repo.md), which explains how to download TPA from Github.com.

### Installing Docker

This tutorial deploys the example deployment onto Docker. If you don't already have Docker installed, you need to set it up.

To install Docker on Debian or Ubuntu:

```
sudo apt update
sudo apt install docker.io
```

For other Linux distributions, see [Install Docker Engine](https://docs.docker.com/engine/install/).

Add your user to the docker group:

```
sudo usermod -aG docker <yourusername>
newgrp docker
```

### Cgroups version

Currently, TPA requires Cgroups Version 1 to be configured on your system.

Run:

```
mount | grep cgroup | head -1
```

If you don't see a reference to `tmpfs` in the output, you need to disable cgroups v2.

To make the appropriate changes, run:

```
echo 'GRUB_CMDLINE_LINUX=systemd.unified_cgroup_hierarchy=false' | sudo tee /etc/default/grub.d/cgroup.cfg
```

Then update Grub and reboot your system:

```
sudo update-grub
sudo reboot
```

!!! Warning
    Giving a user the ability to speak to the Docker daemon
    lets them trivially gain root on the Docker host. Give only trusted users
    access to the Docker daemon.

### Creating a configuration with TPA

The next step is to create a configuration. TPA does most of the work for you by way of its `configure` command. All you have to do is supply command-line flags and options to select, in broad terms, what you want to deploy. Here's the `tpaexec configure` command:

```
tpaexec configure demo --architecture M1 --platform docker --postgresql 15 --enable-repmgr --no-git
```

This command creates a configuration called `demo` that has the [M1 architecture](architecture-M1/). It will therefore have a primary, replica, and backup node.

The `--platform docker` tells TPA to create this configuration on a local Docker instance. It will provision all the containers and OS requirements. Other platforms include [AWS](platform-aws), which does the same with Amazon Web Services, and [Bare](platform-bare), which skips to operating system provisioning and goes straight to installing software on already configured Linux hosts.

The `--postgresql 15` argument instructs TPA to use community Postgres, version 15. There are several options for selecting software, but this is the most straightforward default for open-source users.

Adding `--enable-repmgr` tells TPA to configure the deployment to use [Replication Manager](https://www.repmgr.org/) to handle replication and failover. 

Finally, `--no-git` turns off the feature in TPA that allows you to revision control your configuration using Git.

Run this command, which doesn't return anything at the command line when it's complete. However, a directory called `demo` is created that contains some files. These files include `config.yml`, which is a blueprint for the new deployment.

## Provisioning the deployment

Now you're ready to create the containers (or virtual machines) on which to run the new deployment. Use the `provision` command to achieve this:

```
tpaexec provision demo
```

You will see TPA work through the various operations needed to prepare to deploy your configuration. 

## Deploying

Once the containers are provisioned, you can move on to deployment. Deploying installs, if needed, operating systems and system packages. It then installs the requested Postgres architecture and performs all the needed configuration. 

```
tpaexec deploy demo
```

You will see TPA work through the various operations needed to deploy your configuration.


## Testing

You can quickly test your newly deployed configuration using the tpaexec `test` command. This command runs pgbench on your new database.

```
tpaexec test demo
```

## Connecting

To get to a psql prompt, the simplest route is to log into one of the containers (or VMs or host, depending on configuration) using Docker or SSH. To ping all the connectable hosts in the deployment, run: 

```
tpaexec ping demo
```

The output looks something like:

```
$ tpaexec ping demo 
unfair | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
uptake | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
quondam | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
uptight | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

Select one of the nodes that responded with `SUCCESS`. This tutorial uses `uptake`.

If you're only planning on using Docker, use the command `docker exec -it uptake /bin/bash`, substituting the appropriate hostname.

Another option that works with all types of TPA deployment is to use SSH. To do that, first change current directory to the created configuration directory. 

For example, the tutorial configuration is called `demo`. Go to that directory and run `ssh -F ssh_config ourhostname` to connect:

```
cd demo
ssh -F ssh_config uptake
Last login: Wed Sep  6 10:08:01 2023 from 172.17.0.1
[root@uptake ~]# 
```

In both cases, you're logged in as a root user on the container.

You can now change user to the postgres user using `sudo -iu postgres`. As postgres, you can run psql. TPA has already configured that user with a `.pgpass` file, so you don't need to enter a password.

```
[root@uptake ~]# 
postgres@uptake:~ $ psql
psql (15.4)
Type "help" for help.

postgres=# 
```

You're connected to the database.

You can connect from the host system without using SSH to get into one of the containers. Obtain the IP address of the host you want to connect to from the `ssh_config` file:

```
$ grep "^ *Host" demo/ssh_config 
Host *
Host uptight
    HostName 172.17.0.9
Host unfair
    HostName 172.17.0.4
Host quondam
    HostName 172.17.0.10
Host uptake
    HostName 172.17.0.11
```

You're going to connect to `uptake`, so the IP address is 172.17.0.11. 

You also need to retrieve the password for the postgres user. Run `tpaexec show-password demo postgres` to get the stored password from the system:

```
tpaexec show-password demo postgres
a9LmI1X^uMOpPoEnLuRdL%L$oRQak3om
```

Assuming you have a Postgresql client installed, you can then run:

```
psql --host 172.17.0.11 -U postgres
Password for user postgres: 
```

Enter the password you previously retrieved:

```
psql (14.9 (Ubuntu 14.9-0ubuntu0.22.04.1), server 15.4)
WARNING: psql major version 14, server major version 15.
         Some psql features might not work.
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, bits: 256, compression: off)
Type "help" for help.

postgres=# 
```

You're now connected from the Docker host to Postgres running in one of the TPA-deployed Docker containers.
