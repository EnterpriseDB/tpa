# Configuring /etc/hosts

By default, TPAexec will add lines to /etc/hosts on the target instances
with the IP address and hostname(s) of every instance in the cluster, so
that they can use each other's names for communication within the
cluster (e.g., in `primary_conninfo` for Postgres).

You can specify a list of `extra_etc_hosts_lines` too:

```yaml
instances:
- Name: one
  …
  vars:
    extra_etc_hosts_lines:
    - 192.0.2.1 acid.example.com
    - 192.0.2.2 water.example.com
```

If you don't want the default entries at all, you can specify the
complete list of `etc_hosts_lines` for an instance instead, and only
those lines will be added to /etc/hosts:

```yaml
instances:
- Name: one
  …
  vars:
    extra_etc_hosts_lines:
    - 192.0.2.1 acid.example.com
    - 192.0.2.2 water.example.com
```

If your /etc/hosts doesn't contain the default entries for instances in
the cluster, you'll need to ensure the names can be resolved in some
other way.
