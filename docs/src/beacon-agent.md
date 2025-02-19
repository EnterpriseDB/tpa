---
description: Integrating TPA deployments with EDB Postgres AI using the agent
---

# Configuring the beacon agent

TPA installs and configures the beacon agent on nodes which have
the role `beacon-agent` in `config.yml`. If `--enable-beacon-agent` is
passed to `tpaexec configure`, then all of the postgres nodes in the
cluster have this role.

## Beacon agent package version

By default, TPA installs the latest available version of `beacon-agent`.

The version of the `beacon-agent` package that is installed can be specified 
by including `beacon_agent_package_version: xxx` under the `cluster_vars` 
section of the `config.yml` file.

```yaml
cluster_vars:
    …
    beacon_agent_package_version: '1.56.2-1'
    …
```

You may use any version specifier that apt or yum would accept.

If your version does not match, try appending a `*` wildcard. This
is often necessary when the package version has an epoch qualifier
like `2:...`.


## Beacon agent configuration

The beacon agent configuration contains two parameters which must be set
per-cluster, the access key and the project id.

The access key is kept encrypted in the cluster directory and can be
set or read using tpa's `store-password` and `show-password` commands:

```bash
$ tpaexec store-password . beacon_agent_access_key
Password:
```

```bash
$ tpaexec show-password . beacon_agent_access_key
```

If the environment variable BEACON_AGENT_ACCESS_KEY is set when `tpaexec
provision` is run, the access key is set from its value.

The project id is stored in `config.yml` under the
`beacon_agent_project_id` key in `cluster_vars`. If the
`--beacon_agent_project_id` argument is passed to `tpaexec configure`
then its value is written to `config.yml` appropriately.

## Installing the beacon agent

TPA installs the beacon agent from EDB's repositories and creates an
operating system user called `beacon` and a database user called
`beacon`. A configuration file for the agent is written to
`.beacon/beacon_agent.yaml` in the beacon user's home directory.

## Running the beacon agent

TPA installs a systemd service unit file to start the agent at
boot-time, running as the beacon user.
