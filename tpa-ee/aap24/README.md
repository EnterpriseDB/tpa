# Build an Execution Environment image using script.sh

## choice of base image

TPA provides execution-environment.yml files for both rhel9-minimal-ee and python3.9-alpine base images
depending on your needs.

- rhel9 base image is a RedHat generated image similar to the one provided with AAP2.4 during installation (rhel8-minimal-ee), it is maintained by RedHat and is built to be compatible with AAP2.4.

- python3.9-alpine image is lightweight, minimalist and benefits from alpine's focus on security and docker oriented environment.

## tpa repos ref

Ensure that tpa ref matches the version of TPA in use for your clusters. Using different version will result in unpredictable outcome during cluster deployments.

## build script

TPA provides the build.sh script to help generate EE images based on one of the base image described above.

run the following command to build a RedHat based EE:

```bash
./build.sh --tag tpa-ee:vA.B.C --base-image rhel -v
```

run the following command to build an Alpine based EE:

```bash
./build.sh --tag tpa-ee-alpine:vA.B.C --base-image alpine -v
```

this script will create a python venv, install the build requirements, run ansible-builder that will use the corresponding execution-environment.yml file to generate a docker image usable on AAP 2.4 for TPA deployment.
