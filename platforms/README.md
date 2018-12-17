Platforms
=========

bare
  Servers accessible via SSH (e.g., bare metal, or already-provisioned
  servers on any cloud provider).

aws
  AWS EC2 instances

docker
  Docker containers

lxd
  lxd containers

vagrant
  Vagrant+VirtualBox VMs

Run ``tpaexec info platforms/aws`` (or any of the platform names listed
above) for more information.

Run ``tpaexec configure --architecture M1 --platform aws --help`` to see
the available configure options for the platform (if any).
