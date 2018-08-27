Vagrant
=======

TPAexec supports Vagrant with the VirtualBox provisioner.

Please consult the
[Vagrant documentation](https://www.vagrantup.com/docs/index.html)
if you need help to
[install Vagrant](https://www.vagrantup.com/docs/installation/) and
[get started](https://www.vagrantup.com/intro/getting-started/index.html)
with it.

## Example

```
tpaexec configure foo --architecture M1 --platform vagrant
cd foo
tpaexec provision && vagrant up
tpaexec deploy . -vv
```
