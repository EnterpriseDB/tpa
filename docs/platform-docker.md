# Docker

TPAexec can create Docker containers and deploy a cluster to them. At
present, it sets up containers to run systemd and other services as if
they were ordinary VMs.

## Synopsis

Just select the platform at configure-time:

```bash
[tpa]$ tpaexec configure clustername --platform docker […]
[tpa]$ tpaexec provision clustername
[tpa]$ tpaexec deploy clustername
```

## Operating system selection

Use the standard `--os Debian/Ubuntu/RedHat` configure option to
select which distribution to use for the containers. TPAexec will build
its own systemd-enabled images for this distribution. These images will
be named with a `tpa/` prefix, e.g., `tpa/redhat:8`.

Use `--os-image some/image:name` to specify an existing
systemd-enabled image instead. For example, the
[centos/systemd](https://hub.docker.com/r/centos/systemd/)
image (based on CentOS 7) can be used in this way.

TPAexec does not support Debian 8 (jessie) or Ubuntu 16.04 (xenial) for
Docker containers, because of bugs in the old version of systemd shipped
on those distributions.

## Installing Docker

We test TPAexec with the latest stable Docker-CE packages.

This documentation assumes that you have a working Docker installation,
and are familiar with basic operations such as pulling images and
creating containers.

Please consult the
[Docker documentation](https://docs.docker.com) if you need help to
[install Docker](https://docs.docker.com/install) and
[get started](https://docs.docker.com/get-started/) with it.

On MacOS X, you can [install "Docker Desktop for
Mac"](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)
and launch Docker from the application menu.

### Permissions

TPAexec expects the user running it to have permission to access to the
Docker daemon (typically by being a member of the `docker` group that
owns `/var/run/docker.sock`). Run a command like this to check if you
have access:

```bash
[tpa]$ docker version --format '{{.Server.Version}}'
19.03.12
```

**WARNING**: Giving a user the ability to speak to the Docker daemon
lets them trivially gain root on the Docker host. Only trusted users
should have access to the Docker daemon.

### Docker container privileges

#### Privileged containers

By default TPAexec provisions Docker containers in unprivileged mode, with no
added Linux capabilities flags. Such containers cannot manage host firewall
rules, file systems, block devices, or most other tasks that require true root
privileges on the host.

If you require your containers to run in privileged mode, set the `privileged`
boolean variable for the instance(s) that need it, or globally in
`instance_defaults`, e.g.:

    instance_defaults:
      privileged: true

**WARNING**: Running containers in privileged mode allows the root user or any
process that can gain root to load kernel modules, modify host firewall rules,
escape the container namespace, or otherwise act much as the real host "root"
user would. Do not run containers in priviliged mode unless you really need to.

See `man capabilities` for details on Linux capabilities flags.

#### `security_opts` and the `no-new-privileges` flag

tpaexec can start docker containers in a restricted mode where processes cannot
increase their privileges. setuid binaries are restricted, etc. Enable this in
tpaexec with the `instance_defaults` or per-container variable
`docker_security_opts`:

    instance_defaults:
      docker_security_opts:
        - no-new-privileges

Other arguments to `docker run`'s `--security-opts` are also accepted, e.g.
SELinux user and role.

### Docker storage configuration

**Caution**: The default Docker configuration on many hosts uses
`lvm-loop` block storage and is not suitable for production
deployments. Run `docker info` to check which storage driver you are
using. If you are using the loopback scheme, you will see something
like this:

```
 Storage Driver: devicemapper
  …
  Data file: /dev/loop0
```

Consult the Docker documentation for more information on storage
configuration:

* [Storage Drivers](https://docs.docker.com/storage/storagedriver/)
* [Configuring lvm-direct for production](https://docs.docker.com/storage/storagedriver/device-mapper-driver/#configure-direct-lvm-mode-for-production)
