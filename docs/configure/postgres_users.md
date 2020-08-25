# Creating Postgres users

To create Postgres users during deployment, add entries to the list of
``postgres_users`` under ``cluster_vars`` or a particular instance's
``vars`` in config.yml:

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

Each entry must specify the ``username`` to create.

Any roles in the ``granted_roles`` list will be granted to the
newly-created user.

The ``role_attrs`` list may contain certain
[CREATE ROLE options](https://www.postgresql.org/docs/12/sql-createrole.html)
such as ``[NO]SUPERUSER``, ``[NO]CREATEDB``, ``[NO]LOGIN`` (to create a
user or a role) etc.

## Password generation

By default, TPAexec will generate a random password for the user, and
store it in a vault-encrypted variable named ``<username>_password`` in
the cluster's inventory. You can retrieve the value later:

```bash
$ tpaexec cmd ~/clusters/speedy quirk -m debug -a var=example_password
quirk | SUCCESS => {
    "example_password": "beePh~iez6lie4thi5KaiG%eghaeT]ai"
}
```

(Note: the password may contain characters that are \\-escaped in the
output above. Remember to un-escape them before using the password.)

You cannot explicitly specify a password in config.yml, but you can
define ``<username>_password`` in the inventory yourself instead.

If you don't want the user to have a password at all, you can set
``generate_password: false``.
