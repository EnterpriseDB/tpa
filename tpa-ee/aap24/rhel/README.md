# Generate a RhedHat based TPA compatible Execution environment Image

## the objective

The objective is to generate an execution environment containing all the requirement
for TPA to run deployments of bare platform using Ansible Automation Platform 2.4.

The basic requirements to achieve this are:

- python 3.19 installed and configured
- ansible-runner
- ansible-core-2.15
- TPA source code at the correct tag reference (matching the version you have installed or plan on using on your workstation).

## registry.redhat.io/ansible-automation-platform-24/ee-minimal-rhel9:latest as base image

comes with everything required
python3.9
ansible-runner
ansible-core2.15

only need to add TPA layer.
image provided by Redhat with AAP license

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



