Vagrant
=======

Vagrant is a VM provisioning tool: https://www.vagrantup.com

TPAexec supports Vagrant with the VirtualBox provisioner.

We do not automatically invoke "vagrant up" so that you can run it by
hand and read the output in realtime and debug any problems that may
happen.

## Example

```
tpaexec configure foo --architecture M1 --platform vagrant
cd foo
tpaexec provision && vagrant up
tpaexec deploy . -vv
```
