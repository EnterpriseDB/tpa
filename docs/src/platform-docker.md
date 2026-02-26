---
description: Provisioning and deploying to Docker containers with TPA.
---


# Docker

TPA can create Docker containers and deploy a cluster to them. At
present, it sets up containers to run systemd and other services as if
they were ordinary VMs.

Deploying to docker containers is an easy way to test different cluster
configurations. It is not meant for production use.

## Synopsis

Just select the platform at configure-time:

```shell
tpaexec configure clustername --platform docker […]
tpaexec provision clustername
tpaexec deploy clustername
```

## Operating system selection

Use the standard `--os Debian/Ubuntu/RedHat/SLES` configure option to
select which distribution to use for the containers. TPA will build
its own systemd-enabled images for this distribution. These images will
be named with a `tpa/` prefix, e.g., `tpa/redhat:8`.

Use `--os-image some/image:name` to specify an existing
systemd-enabled image instead. For example, the
[centos/systemd](https://hub.docker.com/r/centos/systemd/)
image (based on CentOS 7) can be used in this way.

## Installing Docker

We test TPA with the latest stable Docker-CE packages.

This documentation assumes that you have a working Docker installation,
and are familiar with basic operations such as pulling images and
creating containers.

Please consult the
[Docker documentation](https://docs.docker.com) if you need help to
[install Docker](https://docs.docker.com/engine/install/) and
[get started](https://docs.docker.com/get-started/) with it.

On MacOS X, you can [install "Docker Desktop for
Mac"](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)
and launch Docker from the application menu.

### Cgroups

All [currently-supported operating systems](distributions.md) provide support cgroups
version 2. You should always use cgroups version 2 on the host machine
when deploying to Docker unless you are using a legacy operating system.

!!! Important 
Instructions for using legacy systems are provided purely for
testing or to support migrating away from those platforms.
!!!

For some legacy platforms, in particular RHEL 7, you will need to
configure your host to use version 1. You can switch to cgroups version
1 as follows.

On Debian-family Linux distributions:
```shell
echo 'GRUB_CMDLINE_LINUX=systemd.unified_cgroup_hierarchy=false' > \
  /etc/default/grub.d/cgroup.cfg
update-grub
reboot
```

On RedHat-family Linux distributions:
```shell
grubby --args=systemd.unified_cgroup_hierarchy=false --update-kernel=ALL
reboot
```
On MacOS:

1. Edit ~/Library/Group\ Containers/group.com.docker/settings.json
   and make the following replacement
   `"deprecatedCgroupv1": false` → `"deprecatedCgroupv1": true`
2. Restart Docker Desktop app

### Permissions

TPA expects the user running it to have permission to access to the
Docker daemon (typically by being a member of the `docker` group that
owns `/var/run/docker.sock`). Run a command like this to check if you
have access:

```shell
docker version --format '{{.Server.Version}}'
```
```output
19.03.12
```

!!! Warning
Giving a user the ability to speak to the Docker daemon
lets them trivially gain root on the Docker host. Only trusted users
should have access to the Docker daemon.
!!!

### Docker container privileges

#### Privileged containers

By default TPA provisions Docker containers in unprivileged mode, with no
added Linux capabilities flags. Such containers cannot manage host firewall
rules, file systems, block devices, or most other tasks that require true root
privileges on the host.

If you require your containers to run in privileged mode, set the `privileged`
boolean variable for the instance(s) that need it, or globally in
`instance_defaults`, e.g.:

```yaml
  instance_defaults:
    privileged: true
```

!!! Warning
Running containers in privileged mode allows the root user or any
process that can gain root to load kernel modules, modify host firewall rules,
escape the container namespace, or otherwise act much as the real host "root"
user would. Do not run containers in priviliged mode unless you really need to.
!!!

See `man capabilities` for details on Linux capabilities flags.

#### `security_opts` and the `no-new-privileges` flag

tpaexec can start docker containers in a restricted mode where processes cannot
increase their privileges. setuid binaries are restricted, etc. Enable this in
tpaexec with the `instance_defaults` or per-container variable
`docker_security_opts`:

```yaml
instance_defaults:
  docker_security_opts:
    - no-new-privileges
```

Other arguments to `docker run`'s `--security-opts` are also accepted, e.g.
SELinux user and role.

#### Linux capabilities flags

tpaexec exposes Docker's control over Linux capabilities flags with the
`docker_cap_add` list variable, which may be set per-container or in
`instance_defaults`. See `man capabilities`, the `docker run` documentation and
the documentation for the Ansible `docker_containers` module for details on
capabilities flags.

Docker's `--cap-drop` is also supported via the `docker_cap_drop` list.

For example, to run a container as unprivileged, but give it the ability to
modify the system clock, you might write:

```yaml
instance_defaults:
  privileged: false
  docker_cap_add:
    - sys_time
  docker_cap_drop:
    - all
```

### Docker storage configuration

The default Docker configuration on many hosts uses
`lvm-loop` block storage and is not suitable for production
deployments. Run `docker info` to check which storage driver you are
using. If you are using the loopback scheme, you will see something
like this:

```output
 Storage Driver: devicemapper
  …
  Data file: /dev/loop0
```

Consult the Docker documentation for more information on storage
configuration:

* [Storage Drivers](https://docs.docker.com/storage/storagedriver/)
* [Configuring lvm-direct for production](https://docs.docker.com/storage/storagedriver/device-mapper-driver/#configure-direct-lvm-mode-for-production)

### Docker MTU settings

By default, Docker networks have a Maximum Transmission Unit (MTU) of
1500 bytes. If this is greater than the MTU of your host system's
network interface you may experience problems routing connections
through that interface to Docker containers. You can check the MTU of
your network interfaces using the command `ipconfig | grep mtu`, 
`ip |grep mtu` or similar. You can change the MTU of a Docker network
provisioned by TPA by adding the appropriate driver options to the
network in `config.yml` as shown below.

```yaml
docker_networks:
- ipam_config:
  - subnet: 10.33.214.192/28
  name: tpa-docker
  driver_options:
    com.docker.network.driver.mtu: 1400
```

!!! Warning
The MTU can only be set when the Docker network is first provisioned.
Subsequent changes in config.yml will have no effect.
!!!

You can verify the MTU of a Docker network by running one of the
commands above from inside a container attached to that network. You can
also use `docker network inspect <network-name> | grep mtu` but this
only works when the MTU has been explicitly set.

## Docker container management

All of the docker containers in a cluster can be started and stopped
together using the `start-containers` and `stop-containers` commands:

```shell
tpaexec start-containers clustername
tpaexec stop-containers clustername
```

These commands don't provision or deprovision containers, or even
connect to them; they are intended to save resources when you're
temporarily not using a docker cluster that you need to keep
available for future use.

For a summary of the provisioned docker containers in a cluster,
whether started or stopped, use the `list-containers` command:

```shell
tpaexec list-containers clustername
```
