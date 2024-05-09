# A First Cluster Deployment

In this short tutorial, we are going to work through deploying a simple [M1 architecture](architecture-M1.md) deployment onto a local Docker installation. By the end you will have four containers, one primary database, two replicas and a backup node, configured and ready for you to explore.

For this example, we will run TPA on an Ubuntu system, but the considerations are similar for most Linux systems.

### Installing TPA

If you're an EDB customer, you'll want to follow the [EDB Repo instructions](INSTALL.md) which will install the TPA packages straight from EDB's repositories.

If you are an open source user of TPA, there's [instructions on how to build from the source](INSTALL-repo.md) which you can download from Github.com.

Follow those guides and then return here.


### Installing Docker

As we said, We are going to deploy the example deployment onto Docker and unless you already have Docker installed we'll need to set that up.

On Debian or Ubuntu, install Docker by running:

```
sudo apt update
sudo apt install docker.io
```

For other Linux distributions, consult the [Docker Engine Install page](https://docs.docker.com/engine/install/).

You will want to add your user to the docker group with:

```
sudo usermod -aG docker <yourusername>
newgrp docker
```

!!! Warning
    Giving a user the ability to speak to the Docker daemon
    lets them trivially gain root on the Docker host. Only trusted users
    should have access to the Docker daemon.

!!! Note on RHEL 7 instances
    To use RHEL 7 instances your host must be configured to run cgroups v1. 
    Refer to documentation for your system to verify and alter cgroups configuration, 
    or choose another operating system for your containers to follow this tutorial.


### Creating a configuration with TPA

The next step in this process is to create a configuration. TPA does most of the work for you through its `configure` command. All you have to do is supply command line flags and options to select, in broad terms, what you want to deploy. Here's our `tpaexec configure` command:

```
tpaexec configure demo --architecture M1 --platform docker --postgresql 15 --enable-repmgr --no-git
```

This creates a configuration called `demo` which has the [M1 architecture](architecture-M1/). It will therefore have a primary, replica and backup node.

The `--platform docker` tells TPA that this configuration should be created on a local Docker instance; it will provision all the containers and OS requirements. Other platforms include [AWS](platform-aws), which does the same with Amazon Web Services and [Bare](platform-bare), which skips to operating system provisioning and goes straight to installing software on already configured Linux hosts.

With `--postgresql 15`, we instruct TPA to use Community Postgres, version 15. There are several options here in terms of selecting software, but this is the most straightforward default for open-source users.

Adding `--enable-repmgr` tells TPA to use configure the deployment to use [Replication Manager](https://www.repmgr.org/) to hand replication and failover. 

Finally, `--no-git` turns off the feature in TPA which allows you to revision control your configuration through git. 

Run this command, and apparently, nothing will happen on the command line. But you will find a directory called `demo` has been created containing some files including a `config.yml` file which is a blueprint for our new deployment.

## Provisioning the deployment

Now we are ready to create the containers (or virtual machines) on which we will run our new deployment. This can be achieved with the `provision` command. Run:

```
tpaexec provision demo
```

You will see TPA work through the various operations needed to prepare for deployment of your configuration. 

## Deploying

Once provisioned, you can move on to deployment. This installs, if needed, operating systems and system packages. It then installs the requested Postgres architecture and performs all the needed configuration. 

```
tpaexec deploy demo
```

You will see TPA work through the various operations needed to deploy your configuration.


## Testing

You can quickly test your newly deployed configuration using the tpaexec `test` command which will run pgbench on your new database.

```
tpaexec test demo
```

## Connecting

To get to a psql prompt, the simplest route is to log into one of the containers (or VMs or host depending on configuration) using docker or SSH. Run 

```
tpaexec ping demo
```

to ping all the connectable hosts in the deployment: You will get output that looks something like:

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

Select one of the nodes which responded with `SUCCESS`. We shall use `uptake` for this example.

If you are only planning on using docker, use the command `docker exec -it uptake /bin/bash`, substituting in the appropriate hostname.

Another option, that works with all types of TPA deployment is to use SSH. To do that, first change current directory to the created configuration directory. 

For example, our configuration is called demo, so we go to that directory. In there, we run `ssh -F ssh_config ourhostname` to connect.

```
cd demo
ssh -F ssh_config uptake
Last login: Wed Sep  6 10:08:01 2023 from 172.17.0.1
[root@uptake ~]# 
```

In both cases, you will be logged in as a root user on the container.

We can now change user to the `postgres` user using `sudo -iu postgres`. As `postgres` we can run `psql`. TPA has already configured that user with a `.pgpass` file so there's no need to present a password.

```
[root@uptake ~]# 
postgres@uptake:~ $ psql
psql (15.4)
Type "help" for help.

postgres=# 
```

And we are connected to our database.

You can connect from the host system without SSHing into one of the containers. Obtain the IP address of the host you want to connect to from the `ssh_config` file.

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

We are going to connect to uptake, so the IP address is 172.17.0.11. 

You will also need to retrieve the password for the postgres user too. Run `tpaexec show-password demo postgres` to get the stored password from the system.

```
tpaexec show-password demo postgres
a9LmI1X^uMOpPoEnLuRdL%L$oRQak3om
```

Assuming you have a Postgresql client installed, you can then run:

```
psql --host 172.17.0.11 -U postgres
Password for user postgres: 
```

Enter the password you previously retrieved.

```
psql (14.9 (Ubuntu 14.9-0ubuntu0.22.04.1), server 15.4)
WARNING: psql major version 14, server major version 15.
         Some psql features might not work.
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, bits: 256, compression: off)
Type "help" for help.

postgres=# 
```

You are now connected from the  Docker host to Postgres running in one of the TPA deployed Docker containers.

