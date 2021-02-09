# Running TPAexec in a Docker container

This document explains how to use a copy of the TPAexec source code
repository to create a docker image/container and use tpaexec instead
of installing the tpaexec package.

Please install TPAexec from packages unless you have been given access
to the TPA source code repository or you have been given a copy of the
source code and specifically advised to use it by 2ndQuadrant.

## Install Docker
If you already have docker installed on your machine, you can skip this
part and simply go to Quickstart.

##
On Mac, download `Docker Desktop for Mac app` and install it. You can 
downoad the latest version from [here](https://desktop.docker.com/mac/stable/Docker.dmg)

Detailed download and installation instructions available on following
link [here](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)

Once installed, simply launch docker from application menu.

## Quickstart

```bash
$ cd /path/to/copy/of/tpaexec
$ docker build -t tpa/tpaexec .
```

To make sure you can provision and control docker containers from within a docker
container i.e. --plaform docker; we create a controller container for tpaexec
that includes functional tpaexec. It basically shares your host docker daemon on
your Mac with tpaexec controller container. This way any docker containers provisioned
from within tpaexec controller container are actually created on your docker host.

```
$ docker run -tid --name="tpaexec-controller" --hostname "tpaexec-controller" -v /var/run/docker.sock:/var/run/docker.sock -v /usr/local/bin/docker:/usr/bin/docker tpa/tpaexec:latest /bin/bash
```

Attach to the container and once connected, you should be able to invoke tpaexec
by simply running `tpaexec` from your terminal.

```bash
$ docker container attach tpaexec-controller
```
Once inside the container, invoke `tpaexec` to verify
```
$ tpaexec selftest
```

If that command completes without any errors, your TPAexec installation
is ready for use.

``
docker run -t hello-world
``

And if that command completes without any errors, your tpaexec-controller container
is correctly setup and ready to provision and control other containers.
