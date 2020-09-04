# pg_ident.conf

You should not normally need to change `pg_ident.conf`, and by default,
TPAexec will not modify it.

You can set `postgres_ident_template` to replace `pg_ident.conf` with
whatever content you like.

```yaml
cluster_vars:
    pg_ident_template: ident.j2
```

You will also need to create `templates/ident.j2` in the cluster
directory:

```jinja2
{% for u in ['unixuser1', 'unixuser2'] %}
mymap {{ u }} dbusername
{% endfor %}
```
