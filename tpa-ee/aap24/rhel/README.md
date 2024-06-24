# Generate a RedHat based TPA compatible Execution environment Image

## Objective

The objective is to generate an execution environment containing all the requirement
for TPA to run deployments of bare platform using Ansible Automation Platform 2.4.

The basic requirements to have a fully functionning Execution Environment are:

- python 3.9
- ansible-runner
- ansible-core-2.15
- TPA source code at the correct tag reference (matching the version you have installed or plan on using on your workstation) tag v23.31 for instance.

## ee-minimal-rhel9:latest as base image

This is the base image chosen for this execution environment. It's an efficient base image which
comes with everything required for a basic execution environment.
- python3.9
- ansible-runner
- ansible-core2.15

The only remaining requirement to meet is to have TPA code added.

The image is generated and maintained by RedHat and is accessible on the registry.redhat.io
It is specificly maintained to be compatible with AAP 2.4, ansible-core version is locked to 2.15.
It's a safe bet for us to avoid broken compatibilities down the line.

## building environment

Building an EE image requires the following environment:

- python
- ansible-builder 3.0
- ansible-navigator

we recommend using python virtual environment (venv).

## environment file

Ansible-builder uses execution-environment.yml to determine the steps needed to generate a Dockerfile
and then build the image.
this one is pretty simple and straightforward, building on the already complete base image.
