---
description: The command that destroys a cluster and associated resources.
---


# tpaexec deprovision

Deprovision destroys a cluster and associated resources.

For a cluster using the `aws` platform, it will remove the instances
and all keypairs, policies, volumes, security groups, route tables,
VPC subnets, internet gateways and VPCs which were set up for the
cluster.

For a cluster using the `docker` platform, it will remove the
containers, any ccache directories which were set up for source builds
in the containers, and any docker networks which were set up for the
cluster.

For all platforms, it will remove all the files created locally by
`tpaexec provision`, including ssh keys, stored passwords, ansible
inventory, and logs.
