# Docker

TPA can create Docker containers and deploy a cluster to them. At
present, it sets up containers to run systemd and other services as if
they were ordinary VMs.

Deploying to Docker containers is an easy way to test different cluster
configurations. It's not meant for production use.

## Synopsis

Select the platform at configure time:

```bash
[tpa]$ tpaexec configure clustername --platform docker […]
[tpa]$ tpaexec provision clustername
[tpa]$ tpaexec deploy clustername
```

## Operating system selection

Use the standard `--os Debian/Ubuntu/RedHat/SLES` configure option to
select the distribution to use for the containers. TPA builds
its own systemd-enabled images for this distribution. These images are
given a `tpa/` prefix, for example, `tpa/redhat:8`.

Use `--os-image some/image:name` to specify an existing
systemd-enabled image instead. For example, you can use the
[centos/systemd](https://hub.docker.com/r/centos/systemd/)
image (based on CentOS 7) in this way.

TPA doesn't support Debian 8 (jessie) or Ubuntu 16.04 (xenial) for
Docker containers because of bugs in the old version of systemd shipped
on those distributions.

## Installing Docker

TPA is tested with the latest stable Docker-CE packages.

This documentation assumes that you have a working Docker installation
and are familiar with basic operations such as pulling images and
creating containers.

See the
[Docker documentation](https://docs.docker.com) if you need help
[installing Docker](https://docs.docker.com/engine/install/) and
[getting started](https://docs.docker.com/get-started/) with it.

On MacOS X, you can [install Docker Desktop for
Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)
and launch Docker from the application menu.

### Cgroups

TPA supports Docker containers on hosts running cgroups version 1 or 2.
On a host running cgroups2, instances running RHEL 7 are not supported.

If you need to use RHEL 7 instances but your host is running cgroups
version 2, you can switch to cgroups version 1 as follows.

On Debian-family Linux distributions:
```
$ echo 'GRUB_CMDLINE_LINUX=systemd.unified_cgroup_hierarchy=false' > \
  /etc/default/grub.d/cgroup.cfg
$ update-grub
$ reboot
```

On RedHat-family Linux distributions:
```
$ grubby --args=systemd.unified_cgroup_hierarchy=false --update-kernel=ALL
$ reboot
```
On MacOS:

1. Edit `~/Library/Group\ Containers/group.com.docker/settings.json`
   and make the following replacement:
   `"deprecatedCgroupv1": false` → `"deprecatedCgroupv1": true`
2. Restart Docker desktop app.

### Permissions

TPA expects the user running it to have permission to access the
Docker daemon, typically by being a member of the `docker` group that
owns `/var/run/docker.sock`. To check if you
have access, run a command like this:

```bash
[tpa]$ docker version --format '{{.Server.Version}}'
19.03.12
```

!!! Warning
    Giving a user the ability to speak to the Docker daemon
    lets them trivially gain root on the Docker host. Give only trusted users
    access to the Docker daemon.

### Docker container privileges

#### Privileged containers

By default, TPA provisions Docker containers in unprivileged mode, with no
added Linux capabilities flags. Such containers can't manage host firewall
rules, file systems, block devices, or most other tasks that require true root
privileges on the host.

If you require your containers to run in privileged mode, set the `privileged`
Boolean variable for the instances that need it, or globally in
`instance_defaults`. For example:

    instance_defaults:
      privileged: true

!!! Warning
    Running containers in privileged mode allows the root user or any
    process that can gain root to load kernel modules, modify host firewall rules,
    escape the container namespace, or otherwise act much as the real host root
    user would. Don't run containers in privileged mode unless you really need to.

See `man capabilities` for details on Linux capabilities flags.

#### `security_opts` and the `no-new-privileges` flag

tpaexec can start Docker containers in a restricted mode in which processes can't
increase their privileges. setuid binaries are restricted, and so on. Enable this ability in
tpaexec with the `instance_defaults` or per-container variable
`docker_security_opts`:

    instance_defaults:
      docker_security_opts:
        - no-new-privileges

Other arguments to `docker run`'s `--security-opts` are also accepted, for example,
SELinux user and role.

#### Linux capabilities flags

tpaexec exposes Docker's control over Linux capabilities flags with the
`docker_cap_add` list variable, which you can set per container or in
`instance_defaults`. See `man capabilities`, the `docker run` documentation, and
the documentation for the Ansible `docker_containers` module for details on
capabilities flags.

Docker's `--cap-drop` is also supported by way of the `docker_cap_drop` list.

For example, to run a container as unprivileged but give it the ability to
modify the system clock, you might write:

    instance_defaults:
      privileged: false
      docker_cap_add:
        - sys_time
      docker_cap_drop:
        - all

### Docker storage configuration

!!! Caution
    The default Docker configuration on many hosts uses
    `lvm-loop` block storage and isn't suitable for production
    deployments. Run `docker info` to check which storage driver you're
    using. If you're using the loopback scheme, you see something
    like this:

    ```
     Storage Driver: devicemapper
      …
      Data file: /dev/loop0
    ```

Consult the Docker documentation for more information on storage
configuration:

* [About storage drivers](https://docs.docker.com/storage/storagedriver/)
* [Configuring lvm-direct for production](https://docs.docker.com/storage/storagedriver/device-mapper-driver/#configure-direct-lvm-mode-for-production)

## Docker container management

You can start and stop all of the Docker containers in a cluster
together using the `start-containers` and `stop-containers` commands:

```bash
[tpa]$ tpaexec start-containers clustername
[tpa]$ tpaexec stop-containers clustername
```

These commands don't provision or deprovision containers, or even
connect to them. They're intended to save resources when you're
temporarily not using a Docker cluster that you need to keep
available for future use.

For a summary of the provisioned Docker containers in a cluster,
whether started or stopped, use the `list-containers` command:

```bash
[tpa]$ tpaexec list-containers clustername
```
