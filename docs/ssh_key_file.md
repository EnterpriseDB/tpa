# ssh_key_file

By default, `tpaexec provision` will use `ssh-keygen` to generate a new
SSH keypair for the cluster (into files named `id_cluster_name` and
`id_cluster_name.pub` inside the cluster directory).

If you want to use an existing key instead, you can set `ssh_key_file`
at the top level of config.yml to the location of an SSH private key
file. The corresponding public key must be available with an extension
of `.pub` at the same location:

```yaml
ssh_key_file: ~/.ssh/id_rsa
```

(If this file does not already exist, it will be created by `ssh-keygen`
during provisioning.)
