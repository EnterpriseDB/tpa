# Running TPAexec in a Docker container

If you are using a system for which there are no [TPAexec
packages](INSTALL.md) available, and it's difficult to run TPAexec after
[installing from source](INSTALL-repo.md) (for example, because it's not
easy to obtain a working Python 3.6+ interpreter), your last resort may
be to build a Docker image and run TPAexec inside a Docker container.

Please note that you do not need to run TPAexec in a Docker container in
order to [deploy to Docker containers](platform-docker.md). It's always
preferable to run TPAexec directly if you can (even on MacOS X).

## Quickstart

You must have Docker installed and working on your system already.

Run the following commands to clone the tpaexec source repository from Github
and build a new Docker image named `tpa/tpaexec`:

```bash
$ git clone https://github.com/EnterpriseDB/tpaexec.git
$ cd tpaexec
$ docker build -t tpa/tpaexec .
```

Double-check the created image:

```bash
$ docker image ls tpa/tpaexec
REPOSITORY    TAG       IMAGE ID       CREATED         SIZE
tpa/tpaexec   latest    e145cf8276fb   8 seconds ago   1.73GB
$ docker rm --rm tpa/tpaexec tpaexec info
# TPAexec v20.11-59-g85a62fe3 (branch: master)
tpaexec=/usr/local/bin/tpaexec
TPA_DIR=/opt/2ndQuadrant/TPA
PYTHON=/opt/2ndQuadrant/TPA/tpa-venv/bin/python3 (v3.7.3, venv)
TPA_VENV=/opt/2ndQuadrant/TPA/tpa-venv
ANSIBLE=/opt/2ndQuadrant/TPA/tpa-venv/bin/ansible (v2.8.15)
```

Create a TPAexec container and make your cluster configuration directories
available inside the container:

```bash
$ docker run --rm -v ~/clusters:/clusters \
    -it tpa/tpaexec:latest
```

You can now run commands like `tpaexec provision /clusters/speedy` at the
container prompt. (When you exit the shell, the container will be removed.)

If you want to provision Docker containers using TPAexec, you must also allow
the container to access the Docker control socket on the host:

```
$ docker run --rm -v ~/clusters:/clusters \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -it tpa/tpaexec:latest
```

Run `docker ps` within the container to make sure that your connection to the
host Docker daemon is working.

## Installing Docker

Please consult the
[Docker documentation](https://docs.docker.com) if you need help to
[install Docker](https://docs.docker.com/install) and
[get started](https://docs.docker.com/get-started/) with it.

On MacOS X, you can [install "Docker Desktop for
Mac"](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)
and launch Docker from the application menu.
