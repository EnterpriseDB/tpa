---
description: The command that destroys a cluster and associated resources.
---


# tpaexec deprovision

Deprovision destroys a cluster and associated resources.

For a cluster using the `aws` platform, it will remove the instances
and all keypairs, policies, volumes, security groups, route tables,
VPC subnets, internet gateways and VPCs which were set up for the
cluster.

For a cluster using the `docker` platform, it will remove the
containers, any ccache directories which were set up for source builds
in the containers, and any docker networks which were set up for the
cluster.

For all platforms, it will remove all the files created locally by
`tpaexec provision`, including ssh keys, stored passwords, ansible
inventory, and logs.

## Retaining ansible.log across deprovision

By default, the cluster directory's `ansible.log` is deleted along with
everything else. If you're iterating on the same cluster directory
(provision, deploy, test, deprovision, repeat) and want to keep each
run's log for comparison, set `ansible_log_rotate: true` at the top
level of `config.yml` (alongside settings like `keyring_backend`, not
under `cluster_vars` - this is local, operator-side behaviour, not a
property of the cluster):

```yaml
ansible_log_rotate: true
```

With this set, deprovision rotates `ansible.log` instead of deleting
it: existing `ansible.log.N` files are shifted up by one, and the
current `ansible.log` becomes `ansible.log.0`. Rotation is unbounded -
older files accumulate until you remove them yourself.

If `config.yml` doesn't set `ansible_log_rotate` at all, the
`ANSIBLE_LOG_ROTATE` environment variable is used instead (accepted
values: `1`, `true`, `yes`, `on`, case-insensitive) - useful for
enabling this for a single command without editing `config.yml`:

```bash
ANSIBLE_LOG_ROTATE=true tpaexec deprovision <cluster_dir>
```

An explicit `ansible_log_rotate` in `config.yml`, `true` or `false`,
always takes precedence over the environment variable.
