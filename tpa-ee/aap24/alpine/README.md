# Generate an python-alpine based TPA compatible Execution environment Image

## the objective

The objective is to generate an execution environment containing all the requirement
for TPA to run deployments of bare platform using Ansible Automation Platform 2.4.

The basic requirements to achieve this are:

- python 3.12 installed and configured
- ansible-runner
- ansible-core-2.16
- TPA source code at the correct tag reference (matching the version you have installed or plan on using on your workstation).

## python:3.12-alpine3.20 as base image

python 3.12 pre-installed and configured.
lightweight and security oriented alpine image helps keep the image size low and is also less subject to CVEs.

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

as well as the use of apk package manager.

```yaml
options:
  package_manager_path: /sbin/apk
build_arg_defaults:
  PKGMGR_PRESERVE_CACHE: 'always'
```

using apk requires to disable the default cache mechanism from ansible-builder which is expecting a yum/dnf based distribution.
This generates a couple more steps to manage manually the cache for apk and pip.

```yaml
   - RUN $PKGMGR cache clean && rm -f /var/cache/apk/*
   - RUN $PYCMD -m pip cache purge
```

alpine image is lightweight, we also need to install gcc to ensure python can build all required wheel files
needed as part of TPA.
