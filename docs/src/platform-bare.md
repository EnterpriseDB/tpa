# bare(-metal servers)

Set `platform: bare` in `config.yml`.

This platform is meant to support any server that's accessible by way of SSH,
including bare-metal servers as well as already-provisioned servers on
any cloud platform (including AWS).

You must define the IP addresses and username for each target server:

```yaml
instances:
  - node: 1
    Name: igor
    platform: bare
    public_ip: 192.0.2.1
    private_ip: 192.0.2.222
    vars:
      ansible_user: xyzzy
```

You must ensure that:

1. TPA can SSH to the instance as `ansible_user`.
2. The `ansible_user` has sudo access on the instance.

## SSH access

In the preceding example, TPA will SSH to `xyzzy@192.0.2.1` to access
the instance.

By default, TPA runs `ssh-keygen` to generate a new SSH keypair
in your cluster directory. The private key is named `id_cluster_name`,
and the public key is stored in `id_cluster_name.pub`.

You must either set `ssh_key_file: /path/to/id_keyname` to use a
different key that the instance will accept, or configure the instance
to allow access from the generated key. For example, use `ssh-copy-id`, which
appends the contents of `id_cluster_name.pub` to
`~xyzzy/.ssh/authorized_keys`.

You must also ensure that SSH can verify the host keys of the
instance. You can add entries to the `known_hosts` file in your
cluster directory. Or, you can install the TPA-generated host keys from
`hostkeys/ssh_host_*_key*` in your cluster directory into `/etc/ssh` on
the instance. (The generated `tpa_known_hosts` file contains entries for
these keys.)

For example, to SSH in with the generated user key but keep the
existing host keys, you can use:

```bash
$ cd ~/clusters/speedy
$ ssh-copy-id -i id_speedy xyzzy@192.0.2.1
$ ssh-keyscan -H 192.0.2.1 >> tpa_known_hosts
```

Run `tpaexec ping ~/clusters/speedy` to check if it's working. If not,
append `-vvv` to the command to look at the complete SSH command-line.

!!! Note
    Ansible invokes SSH to execute a command like
    `bash -c 'python3 && sleep 0'` on the instance. If you run SSH commands
    by hand while debugging, replace this with a command that produces some
    output and then exits instead, for example, `'id'`.

For more details, see:

* [Use a different SSH key](ssh_key_file.md)
* [Manage SSH host keys for bare instances](manage_ssh_hostkeys.md)

## Distribution support

TPA tries to detect the distribution running on target instances
and fails if it isn't supported. TPA currently supports Debian
(8/9/10 or jessie/stretch/buster), Ubuntu (16.04/18.04/20.04/22.04 or
xenial/bionic/focal/jammy), and RHEL/CentOS/Rocky/AlmaLinux (7.x/8.x) on `bare` instances.

## IP addresses

You can specify a `public_ip`, `private_ip`, or both for any instance.

TPA uses these IP addresses in two ways: 

-  To SSH to the instance to execute commands during deployment
-  To set up communications within the cluster, for example, for `/etc/hosts` or to set
`primary_conninfo` for Postgres

If you specify a `public_ip`, it's used to SSH to the instances
during deployment. If you specify a `private_ip`, it's used to set
up communications within the cluster. If you specify both, the
`public_ip` is used during deployment and the `private_ip` for
cluster communications.

If you specify only one or the other, the address is used for both
purposes. For example, you can set only `public_ip` for servers on
different networks or only `private_ip` if you're running TPA
inside a closed network. (If you need to specify only one IP address,
instead of using public/private, you can set `ip_address`.)

## Starting afresh

To start afresh with a cluster on the `bare` platform, use the appropriate
external tools to reinstall, reimage, or reprovision the servers, and
repeat the process covered in this topic. If your new servers have
different IP addresses, or if you have a complex SSH setup, it might be
easier to run [tpaexec deprovision](tpaexec-deprovision.md) to remove all
the locally created files and then [tpaexec provision](tpaexec-provision.md)
to recreate them, followed by repeating the process in this topic.
