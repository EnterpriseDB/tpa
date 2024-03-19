# Environment

You can set `target_environment` to specify environment variables for
TPA to set on the target instances during deployment. For example, you can
specify an HTTPS proxy:

```
cluster_vars:
    target_environment:
        https_proxy: https://proxy.example:8080
```

TPA ensures these settings, along with any others it needs, are present
in the environment during deployment and the later execution of
any cluster management commands.

These environment settings don't persist, but you can instead use
[`extra_bashrc_lines`](postgres_user.md) to set environment variables
for the postgres user.
