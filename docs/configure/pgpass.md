# Configuring .pgpass

TPAexec will create `~postgres/.pgpass` by default with the passwords
for `postgres` and `repmgr` in it, for use between cluster instances.
You can set `pgpass_users` to create entries for a different list of
users.

You can also include the `postgres/pgpass` role from hook scripts to
create your own `.pgpass` file:

```yaml
- include_role: name=postgres/pgpass
  vars:
    pgpassfile: ~otheruser/.pgpass
    pgpass_owner: otheruser
    pgpass_group: somegroup
    pgpass_users:
    - xyzuser
    - pqruser
```
