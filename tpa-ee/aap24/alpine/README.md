# Generate a RhedHat based TPA compatible Execution environment Image

## the objective

The objective is to generate an execution environment containing all the requirement
for TPA to run deployments of bare platform using Ansible Automation Platform 2.4.

The basic requirements to achieve this are:

- python 3.19 installed and configured
- ansible-runner
- ansible-core-2.15
- TPA source code at the correct tag reference (matching the version you have installed or plan on using on your workstation).

## python:3.9-alpine3.19 as base image

python 3.9 pre-installed and configured.
smallest and most up to date security wise.

## requirements

Building an execution image requires the following environment:

python
ansible-builder
ansible-navigator


## environment file

tpa-exec-ee.yml

## .dockerignore file

lists files part of TPA repo that is not required for the EE image

## Build the image

build.sh script

```bash
./build.sh --tag registry_address/namespace/tpa-ee:vA.B.C
```



