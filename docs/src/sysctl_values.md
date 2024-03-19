# Setting sysctl values

By default, TPA sets various sysctl values on target instances and
includes them in `/etc/sysctl.conf` so that they persist across reboots.

You can optionally specify your own values in `sysctl_values`:

```yaml
cluster_vars:
  sysctl_values:
    kernel.core_pattern: core.%e.%p.%t
    vm.dirty_bytes: 4294967296
    vm.zone_reclaim_mode: 0
```

Values you specify take precedence over any TPA default
values for that variable. First add the settings to
`sysctl.conf`, each on its own line. Then load them with `sysctl -p`.

Docker and lxd instances don't support setting sysctl values, so TPA
skips this step for those platforms.
