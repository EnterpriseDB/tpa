---
description: Setting sysctl values for target instances.
---


# Setting sysctl values

TPA writes its managed sysctl settings to `/etc/sysctl.d/30-tpa.conf`.
The settings persist across reboots and can be reloaded at any time
with `sysctl --system`. To override any of them, drop a file with a
higher numeric prefix under `/etc/sysctl.d/` (for example,
`/etc/sysctl.d/90-local.conf`): `sysctl --system` loads files in
lexical order, so later definitions win. You don't need to round-trip
through `config.yml` to do this.

Docker and lxd instances don't support setting sysctls, so TPA will
skip this step altogether for those platforms.

## What TPA manages

TPA's managed settings fall into three groups:

* **Baseline** — currently just `kernel.core_pattern`, which sets a
  consistent core-dump path. Always written when the `sysctl` task
  runs.

* **`sysctl_vm`** — Postgres-specific kernel tuning (the `vm.dirty_*`
  family and `vm.zone_reclaim_mode`). Applied by default; opt out
  by adding `sysctl_vm` to `excluded_tasks`.

* **`sysctl_net`** — busy-server network tuning (`net.core.rmem_max`,
  `net.core.wmem_max`, `net.ipv4.tcp_max_syn_backlog`,
  `net.ipv4.ip_local_port_range`). These have to be opted in to
  explicitly because the right values depend on workload
  characteristics that only the operator knows. Opt in by adding
  `sysctl_net` to `opt_in_tasks`. `tpaexec configure --platform
  aws` opts the cluster in automatically; bare-metal clusters stay
  opted out by default.

So a typical bare-metal cluster gets the baseline plus `sysctl_vm`,
and a typical AWS cluster gets all three. On an AWS cluster you can
opt out of `sysctl_net` again by editing `config.yml`:

```yaml
cluster_vars:
  excluded_tasks:
    - sysctl_net
```

## Overriding TPA's values via config.yml

You can also override individual settings — from any group — by
listing them in `sysctl_values`:

```yaml
cluster_vars:
  sysctl_values:
    vm.dirty_bytes: 8589934592
    net.core.somaxconn: 16384
```

`sysctl_values` entries are written after the TPA defaults, so they
win. This route is convenient if you want to manage a couple of
overrides as part of your cluster definition; for ad-hoc or
operationally-imposed values, dropping a file in `/etc/sysctl.d/` on
the host directly is usually simpler.

## Hugepages

By default, TPA reserves hugepages of the architecture's default size
(2MB on x86_64) for Postgres to use for `shared_buffers`. It does this
by adding `hugepages=N` to the kernel command line and writing
`vm.nr_hugepages = N` to the `sysctl_vm` section of
`/etc/sysctl.d/30-tpa.conf`.

If you want Postgres to use a larger hugepage size (typically 1GB on
x86_64), set `huge_page_size` to a Postgres-style memory string:

```yaml
instances:
- Name: primary
  vars:
    huge_page_size: 1GB
```

When `huge_page_size` is set, TPA will:

* reserve pages of that size on the kernel command line, e.g.
  `hugepagesz=1G hugepages=N`;
* omit `vm.nr_hugepages` from `/etc/sysctl.d/30-tpa.conf` (that sysctl
  only ever applies to the architecture's default-size pool, and is
  silently ineffective for any other size); and
* set the `huge_page_size` GUC in `postgresql.conf` so Postgres uses
  pages from the chosen pool.

It is almost always right to set `huge_page_size` on individual Postgres
instances rather than in `cluster_vars`: any reservation made on the
kernel command line is taken out of normal memory at boot, so a Barman
server or other non-Postgres instance in the same cluster does not want
the same allocation as a Postgres node.

By default, TPA calculates the number of hugepages to reserve as
`shared_buffers` plus 3% of total RAM, divided by the hugepage size.
You can override this calculation by setting `nr_hugepages` directly:

```yaml
instances:
- Name: primary
  vars:
    huge_page_size: 1GB
    nr_hugepages: 16
```

!!! Note
For backwards compatibility, an existing
`sysctl_values['vm.nr_hugepages']` is honoured as the page count when
`nr_hugepages` is not set explicitly.
!!!

!!! Note
Note that updating the kernel command line on an already-deployed
instance is outside TPA's scope: changing `huge_page_size` or
`nr_hugepages` after the first deploy will not rewrite the existing
GRUB configuration. Edit it by hand and reboot to apply the change.
!!!

## Transparent hugepages

By default, TPA will set transparent_hugepage to "never" on the kernel
command line and also install a script, `/etc/tpa/rc.local`, to set it
at boot-time via the `sys` filesystem. To use a different setting, set
`transparent_hugepage` to `always` or `madvise` in an instances `vars`
or in `cluster_vars` to control all instances.
