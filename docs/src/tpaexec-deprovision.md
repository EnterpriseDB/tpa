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
run's log for comparison, set `preserve_ansible_log: true` at the top
level of `config.yml` (alongside settings like `keyring_backend`, not
under `cluster_vars` - this is local, operator-side behaviour, not a
property of the cluster):

```yaml
preserve_ansible_log: true
```

With this set, deprovision preserves `ansible.log` instead of deleting
it: the current `ansible.log` is renamed to `ansible.log.N`, where `N`
is one more than the highest suffix already present (or `0` if there
are no `ansible.log.N` files yet). Existing `ansible.log.N` files are
left untouched under their original names, so each run keeps a stable
filename you can refer back to. Accumulation is unbounded - older
files stay until you remove them yourself.

If `config.yml` doesn't set `preserve_ansible_log` at all, the
`PRESERVE_ANSIBLE_LOG` environment variable is used instead (accepted
values: any string Ansible's `bool` filter recognizes as true/false -
`yes`/`no`, `true`/`false`, `1`/`0`, `on`/`off`, case-insensitive) -
useful for enabling this for a single command without editing
`config.yml`:

```bash
PRESERVE_ANSIBLE_LOG=true tpaexec deprovision <cluster_dir>
```

An explicit `preserve_ansible_log` in `config.yml`, `true` or `false`,
always takes precedence over the environment variable.
