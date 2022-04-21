# Managing SSH host keys

TPAexec generates a set of SSH host keys while provisioning a cluster.
These keys are stored in the cluster directory, under the `hostkeys`
subdirectory. These host keys are automatically installed into
`/etc/ssh` on AWS EC2 instances and Docker containers.

By default, these host keys are not installed on
[bare instances](platform-bare.md),
but you can set `manage_ssh_hostkeys` to enable it:

```yaml
instances:
- Name: one
  …
  platform: bare
  vars:
    manage_ssh_hostkeys: yes
```

You must initially set up `known_hosts` in your cluster directory with
correct entries, as described in the docs for
[bare instances](platform-bare.md). TPAexec will replace the host keys
during deployment.

The `manage_ssh_hostkeys` setting is meaningful only for bare instances.
The generated host keys will be installed on all other instances.

## known_hosts

TPAexec will add entries for every host and its public host keys to the
global `ssh_known_hosts` file on every instance in the cluster, so that
they can ssh to each other without host key verification prompts,
regardless of whether they have `manage_ssh_hostkeys` set or not.
