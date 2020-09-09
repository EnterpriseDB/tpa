# bare(-metal servers)

Set `platform: bare` in config.yml

This platform is meant to support any server that is accessible via SSH,
including bare-metal servers as well as already-provisioned servers on
any cloud platform (including AWS).

You must define the IP address(es) and username for each target server:

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

You must ensure that

1. TPAexec can ssh to the instance as `ansible_user`
2. The `ansible_user` has sudo access on the instance

## SSH access

In the example above, TPAexec will ssh to `xyzzy@192.0.2.1` to access
the instance.

By default, TPAexec will run `ssh-keygen` to generate a new SSH keypair
in your cluster directory. The private key is named `id_cluster_name`
and the public key is stored in `id_cluster_name.pub`.

You must either set `ssh_key_file: /path/to/id_keyname` to use a
different key that the instance will accept, or configure the instance
to allow access from the generated key (e.g., use `ssh-copy-id`, which
will append the contents of `id_cluster_name.pub` to
`~xyzzy/.ssh/authorized_keys`).

You must also ensure that ssh can verify the host key(s) of the
instance. You can either add entries to the `known_hosts` file in your
cluster directory, or install the TPAexec-generated host keys from
`hostkeys/ssh_host_*_key*` in your cluster directory into `/etc/ssh` on
the instance (the generated `tpa_known_hosts` file contains entries for
these keys).

For example, to ssh in with the generated user key, but keep the
existing host keys, you can do:

```bash
$ cd ~/clusters/speedy
$ ssh-copy-id -i id_speedy xyzzy@192.0.2.1
$ ssh-keyscan -H 192.0.2.1 >> tpa_known_hosts
```

Run `tpaexec ping ~/clusters/speedy` to check if it's working. If not,
append `-vvv` to the command to look at the complete ssh command-line.
(Note: Ansible will invoke ssh to execute a command like
`bash -c 'python3 && sleep 0'` on the instance. If you run ssh commands
by hand while debugging, replace this with a command that produces some
output and then exits instead, e.g., `'id'`.)

## Distribution support

TPAexec will try to detect the distribution running on target instances,
and fail if it is not supported. TPAexec currently supports Debian
(8/9/10; or jessie/stretch/buster), Ubuntu (16.04/18.04/20.04; or
xenial/bionic/focal), and RHEL/CentOS (7.x/8.x) on `bare` instances.
