# The postgres Unix user

You can configure the postgres user and its home directory.

For information about how to create Postgres users in the database, see
[Creating Postgres users](postgres_users.md).

## Shell configuration

TPA installs a `.bashrc` file and ensures that it's also included
by the `.profile` or `.bash_profile` files.

It sets a prompt that includes the username, hostname, and working
directory and ensures that `postgres_bin_dir` is in the `PATH`. It also sets
`PGDATA` to the location of `postgres_data_dir`.

You can optionally specify `extra_bashrc_lines` to append arbitrary
lines to `.bashrc`. (To avoid having to worry about quoting and 
escaping shell meta-characters, Use the YAML multi-line string syntax `>-`.)

```yaml
cluster_vars:
  extra_bashrc_lines:
  - alias la=ls\ -la
  - >-
    export PATH="$PATH":/some/other/dir
```

TPA edits `sudoers` to allow
`sudo systemctl start/stop/reload/restart/status postgres`. It also
changes `ulimits` to allow unlimited core dumps and raises the file
descriptor limits.

## SSH keys

TPA uses `ssh-keygen` to generate and install an SSH keypair for
the postgres user. It also edits `.ssh/authorized_keys` so that the instances
in the cluster can SSH to each other as postgres.

## TLS certificates

By default, TPA generates a private key and a self-signed TLS
certificate for use in the cluster. This is sufficient to ensure
that traffic between clients and server is encrypted in transit. If
you want to use your own certificate-signing infrastructure, you can
replace these after deployment is complete, or replace them during
deployment using a [hook](tpaexec-hooks.md).

## Username

The `postgres_user` and `postgres_group` settings (both `postgres` by
default) are used consistently everywhere. You can change them if you
need to run Postgres as a different user.
