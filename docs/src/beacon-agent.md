# Configuring the beacon agent

TPA installs and configures the beacon agent on nodes which have
the role `beacon-agent` in `config.yml`. If `--enable-beacon-agent` is
passed to `tpaexec configure`, then all of the postgres nodes in the
cluster have this role.

## beacon agent configuration

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

## installing the beacon agent

TPA installs the beacon agent from EDB's repositories and creates an
operating system user called `beacon` and a database user called
`beacon`. A configuration file for the agent is written to
`.beacon/beacon_agent.yaml` in the beacon user's home directory.

## running the beacon agent

TPA installs a systemd service unit file to start the agent at
boot-time, running as the beacon user.
