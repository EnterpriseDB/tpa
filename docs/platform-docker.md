# Docker

TPAexec has support for Docker.

## Basic usage

It is generally sufficient to ensure that the user running `tpaexec` has access
to the Docker daemon. Then pass `--platform docker` to `tpaexec configure`.
All later TPAexec operations on the created cluster will use Docker instead of
the default platform.

## Guest operating system support

At the moment, the Docker tpaexec platform supports only the
[centos/systemd](https://hub.docker.com/r/centos/systemd/)
image (based on CentOS 7). No other options are accepted
for `--os` at this time.

## Installing Docker

You do not need the Docker.io Docker distribution; it is generally sufficient
to install a Linux distribution's Docker packages, e.g.:

    sudo yum install docker
    sudo systemctl start docker

Please consult the
[Docker documentation](https://docs.docker.com) if you need help to
[install Docker](https://docs.docker.com/install) and
[get started](https://docs.docker.com/get-started/) with it.

The [Ansible module documentation](https://docs.ansible.com/ansible/latest/modules/docker_container_module.html)
may also be helpful.

### Docker storage configuration

**Caution**: The default Docker configuration on many hosts uses `lvm-loop`
block storage and is not suitable for production deployments. Check `docker
info` to see what storage drivers you are using. If you see:

    Storage Driver: devicemapper
      ...
      Data file: /dev/loop0
      ...

...or similar, you're using the loopback scheme. See the Docker documentation
for more information on storage configuration:

* [Storage Drivers](https://docs.docker.com/storage/storagedriver/)
* [Configuring lvm-direct for production](https://docs.docker.com/storage/storagedriver/device-mapper-driver/#configure-direct-lvm-mode-for-production)

### Docker access privileges

TPAexec requires that it be able to communicate with the Docker daemon without
any privilege-elevating command like `sudo`.

Check that a user can access the Docker daemon by running:

    docker version --format '{{.Server.Version}}'

Users normally access `dockerd` via the unix socket `/var/run/docker.sock`,
which is usually owned by group `docker`. So you can add a user to the `docker`
group to let them use Docker with TPAexec:

    sudo usermod -a -G docker "$(id -un)"

**BEWARE**: Giving a user the ability to control the Docker daemon lets them
trivially gain root on the Docker host. Only give trusted users access to the
Docker daemon.

## Advanced TPAexec options

The `--os-image` option to `tpaexec configure` may be used to provide a
pre-built base image preloaded with site-specific repositories, pre-installed
dependencies, etc.

Care must be taken to ensure that anything preinstalled does not conflict with
whatever setup TPAexec does during provisioning and deployment. In particular,
you should not preinstall PostgreSQL on your base images - but installing
PostgreSQL's dependencies can be useful. So pre-populating the yum cache
with PostgreSQL packages can be useful.
