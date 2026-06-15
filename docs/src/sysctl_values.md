---
description: Setting sysctl values for target instances.
---


# Setting sysctl values

By default, TPA sets various sysctl values on target instances, and
includes them in `/etc/sysctl.conf` so that they persist across reboots.

You can optionally specify your own values in `sysctl_values`:

```yaml
cluster_vars:
  sysctl_values:
    kernel.core_pattern: core.%e.%p.%t
    vm.dirty_bytes: 4294967296
    vm.zone_reclaim_mode: 0
```

Any values you specify will take precedence over TPA's default
values for that variable (if any). The settings will first be added to
`sysctl.conf` line-by-line, and finally loaded with `sysctl -p`.

Docker and lxd instances do not support setting sysctls, so TPA will
skip this step altogether for those platforms.

## Hugepages

By default, TPA reserves hugepages of the architecture's default size
(2MB on x86_64) for Postgres to use for `shared_buffers`. It does this
by adding `hugepages=N` to the kernel command line and writing
`vm.nr_hugepages = N` to `/etc/sysctl.conf`.

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
* omit `vm.nr_hugepages` from `/etc/sysctl.conf` (that sysctl only ever
  applies to the architecture's default-size pool, and is silently
  ineffective for any other size); and
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
