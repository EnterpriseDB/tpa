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
