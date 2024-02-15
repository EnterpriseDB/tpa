# Configuring /etc/hosts

By default, TPA adds lines to `/etc/hosts` on the target instances
with the IP address and hostnames of every instance in the cluster. This
enables the instances to use each other's names for communication within the
cluster (for example, in `primary_conninfo` for Postgres).

You can specify a list of `extra_etc_hosts_lines`, too:

```yaml
instances:
- Name: one
  …
  vars:
    extra_etc_hosts_lines:
    - 192.0.2.1 acid.example.com
    - 192.0.2.2 water.example.com
```

If you don't want any of the default entries, you can specify the
complete list of `etc_hosts_lines` for an instance instead. Add only
those lines to `/etc/hosts`:

```yaml
instances:
- Name: one
  …
  vars:
    etc_hosts_lines:
    - 192.0.2.1 acid.example.com
    - 192.0.2.2 water.example.com
    - 192.0.2.3 base.example.com
```

If your `/etc/hosts` doesn't contain the default entries for instances in
the cluster, you need to ensure the names can be resolved in some
other way.
