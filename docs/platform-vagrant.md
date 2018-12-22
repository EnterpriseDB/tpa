Vagrant
=======

TPAexec supports Vagrant with the VirtualBox provisioner.

Please consult the
[Vagrant documentation](https://www.vagrantup.com/docs/index.html)
if you need help to
[install Vagrant](https://www.vagrantup.com/docs/installation/) and
[get started](https://www.vagrantup.com/intro/getting-started/index.html)
with it.

At the moment, this platform supports Debian 9 (stretch), CentOS 7, and
Ubuntu 16.04 (Xenial).

## Example

```
[tpa]$ tpaexec configure foo --architecture M1 --platform vagrant
[tpa]$ cd foo
[tpa]$ tpaexec provision && vagrant up
[tpa]$ tpaexec deploy . -vv
```

TPAexec will not automatically invoke "vagrant up", so that you can run
it by hand and read the output in realtime and debug any problems that
may happen.
