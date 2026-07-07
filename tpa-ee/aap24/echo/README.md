# Generate an Echo (Debian-based) TPA compatible Execution environment Image

## the objective

The objective is to generate an execution environment containing all the requirement
for TPA to run deployments of bare platform using Ansible Automation Platform 2.4.

The basic requirements to achieve this are:

- python 3.12 installed and configured
- ansible-runner
- ansible-core-2.16
- TPA source code at the correct tag reference (matching the version you have installed or plan on using on your workstation).

## reg.echohq.com/python:3.12-slim as base image

python 3.12 pre-installed and configured (built under `/usr/local`).
This is "Echo Linux", a Debian-derivative (`ID_LIKE=debian`, apt-based) published
on the internal `reg.echohq.com` registry. The `slim` variant keeps the footprint
low while giving us a glibc base, so most Python dependencies (`cryptography`,
`cffi`, `psutil`, ...) install from prebuilt manylinux wheels rather than
compiling from source.

The suffix-less `3.12-slim` tag tracks whatever Debian release the upstream
python image currently defaults to (Bookworm/Trixie depending on the mirror
snapshot). This is not a concern here: `apt-get` and the system packages we
install are stable across those releases. Run `cat /etc/os-release` inside the
built image if you need to know the exact codename.

## requirements

Building an execution image requires the following environment:

- python3
- ansible-builder
- ansible-navigator

## environment file

Ansible-builder uses execution-environment.yml to determine the steps needed to generate a Dockerfile
and then build the image.
The noticeable addition to this file is the definition of ansible-core 2.16.*

```yaml
  ansible_core:
    package_pip: ansible-core==2.16.*
```

as well as the use of the apt package manager.

```yaml
options:
  package_manager_path: /usr/bin/apt-get
build_arg_defaults:
  PKGMGR_PRESERVE_CACHE: 'always'
```

using apt requires to disable the default cache mechanism from ansible-builder which is expecting a yum/dnf based distribution.
This generates a couple more steps to manage manually the apt and pip caches.

```yaml
   - RUN $PKGMGR clean && rm -rf /var/lib/apt/lists/*
   - RUN $PYCMD -m pip cache purge
```

We also install a compiler toolchain (`gcc`, `build-essential`, `libffi-dev`) so
that python can build any wheel that is not available prebuilt, plus
`openssh-client` and `git` needed as part of TPA.

## building

From `tpa-ee/aap24/`:

```bash
./build.sh -b echo -t tpa-ee:echo
```
