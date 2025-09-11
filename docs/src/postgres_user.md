---
description: How TPA configures the Postgres system user
---

# The postgres Unix user

This page documents how the postgres user and its home directory are
configured.

There's a separate page about how to create
[Postgres users in the database](postgres_users.md).

## Shell configuration

TPA will install a `.bashrc` file and ensure that it's also included
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

TPA will use `ssh-keygen` to generate and install an SSH keypair for
the postgres user, and edit `.ssh/authorized_keys` so that the instances
in the cluster can ssh to each other as `postgres`.

## TLS certificates

By default, TPA will generate a private key and a self-signed TLS
certificate which are used by Postgres as the `ssl_key_file` and
`ssl_cert_file` respectively. The files are named using the TPA cluster
name (`cluster_name.key` and `cluster_name.crt`) and located in
`/etc/tpa`. For more information, including how to provide your own
key and certificate, see the documentation for 
[postgresql.conf](postgresql.conf.md#ssl-configuration).

The size of self-signed TLS key can be modified adding the variable `postgres_rsa_key_size`
to the `cluster_vars` section:

```yml
  (...)
  cluster_vars:
    postgres_rsa_key_size: 4096
```

## Username

The `postgres_user` and `postgres_group` settings (both `postgres` by
default) are used consistently everywhere. You can change them if you
need to run Postgres as a different user for some reason.
