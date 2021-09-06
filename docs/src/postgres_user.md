# The postgres Unix user

This page documents how the postgres user and its home directory are
configured.

There's a separate page about how to create
[Postgres users in the database](postgres_users.md).

## Shell configuration

TPAexec will install a `.bashrc` file and ensure that it's also included
by the `.profile` or `.bash_profile` files.

It will set a prompt that includes the username and hostname and working
directory, and ensure that `postgres_bin_dir` in in the `PATH`, and set
`PGDATA` to the location of `postgres_data_dir`.

You can optionally specify `extra_bashrc_lines` to append arbitrary
lines to `.bashrc`. (Use the YAML multi-line string syntax `>-` to avoid
having to worry about quoting and escaping shell metacharacters.)

```yaml
cluster_vars:
  extra_bashrc_lines:
  - alias la=ls\ -la
  - >-
    export PATH="$PATH":/some/other/dir
```

It will edit sudoers to allow
`sudo systemctl start/stop/reload/restart/status postgres`, and also
change `ulimits` to allow unlimited core dumps and raise the file
descriptor limits.

## SSH keys

TPAexec will use `ssh-keygen` to generate and install an SSH keypair for
the postgres user, and edit `.ssh/authorized_keys` so that the instances
in the cluster can ssh to each other as `postgres`.

## TLS certificates

By default, TPAexec will generate a private key and a self-signed TLS
certificate for use within the cluster. If you create `cluster_name.key`
and `cluster_name.crt` files within your cluster directory, it will use
that key and certificate instead of generating one.

We strongly recommend either using the self-signed certificate
(perfectly sufficient to ensure that traffic between clients and server
is encrypted in transit) or making some more secure alternative
arrangement to install the TLS private key and certificate on the
instances (where the private key does not leave the instances). The
details depend on your certificate-signing infrastructure.

## Username

The `postgres_user` and `postgres_group` settings (both `postgres` by
default) are used consistently everywhere. You can change them if you
need to run Postgres as a different user for some reason.
