# Environment

You can set `target_environment` to specify environment variables that
TPAexec should set on the target instances during deployment (e.g., to
specify an HTTPS proxy, as shown below).

```
cluster_vars:
    target_environment:
        https_proxy: https://proxy.example:8080
```

TPAexec will ensure these settings are present in the environment (along
with any others it needs) during deployment and the later execution of
any cluster management commands.

These environment settings are not persistent, but you can instead use
[`extra_bashrc_lines`](postgres_user.md) to set environment variables
for the postgres user.
