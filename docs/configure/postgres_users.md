# Creating Postgres users

To create Postgres users during deployment, add entries to the list of
`postgres_users` under `cluster_vars` or a particular instance's
`vars` in config.yml:

```yaml
cluster_vars:
  postgres_users:
  - username: example

  - username: otheruser
    generate_password: true
    role_attrs:
    - superuser
    - replication
    granted_roles:
    - r1
    - r2
```

The example above would create two users (apart from any users that
TPAexec itself decides to create, such as repmgr or barman).

Each entry must specify the `username` to create.

Any roles in the `granted_roles` list will be granted to the
newly-created user.

The `role_attrs` list may contain certain
[CREATE ROLE options](https://www.postgresql.org/docs/12/sql-createrole.html)
such as `[NO]SUPERUSER`, `[NO]CREATEDB`, `[NO]LOGIN` (to create a
user or a role) etc.

## Password generation

By default, TPAexec will generate a random password for the user, and
store it in a vault-encrypted variable named `<username>_password` in
the cluster's inventory. You can retrieve the value later:

```bash
$ tpaexec show-password ~/clusters/speedy example
beePh~iez6lie4thi5KaiG%eghaeT]ai
```

You cannot explicitly specify a password in config.yml, but you can
store a different `<username>_password` in the inventory instead:

```bash
$ tpaexec store-password ~/clusters/speedy example --random
$ tpaexec show-password ~/clusters/speedy example
)>tkc}}k1y4&epaJ?;NJ:l'uT{C7D*<p
$ tpaexec store-password ~/clusters/speedy example
Password:
$ tpaexec show-password ~/clusters/speedy example
terrible insecure password
$
```

If you don't want the user to have a password at all, you can set
`generate_password: false`.
