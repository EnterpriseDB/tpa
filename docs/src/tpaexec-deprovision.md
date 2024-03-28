# tpaexec deprovision

Deprovision destroys a cluster and associated resources.

For all platforms, it removes all the files created locally by
`tpaexec provision`, including SSH keys, stored passwords, Ansible
inventory, and logs.

For a cluster using the `aws` platform, it remove the instances
and all keypairs, policies, volumes, security groups, route tables,
VPC subnets, internet gateways, and VPCs that were set up for the
cluster.

For a cluster using the `docker` platform, it removes the
containers, any ccache directories that were set up for source builds
in the containers, and any Docker networks that were set up for the
cluster.
