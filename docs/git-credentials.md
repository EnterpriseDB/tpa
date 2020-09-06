# Git credentials

This page explains how to clone Git repositories that require
authentication.

This may be required when you change `postgres_git_url`
to [install Postgres from source](postgres_installation_method_src.md) or
[use `install_from_source`](install_from_source.md) to compile and
install extensions.

You have two options to authenticate without writing the credentials to
disk on the target instance:

* For an `ssh://` repository, you can add an SSH key to your local
  ssh-agent. Agent forwarding is enabled by default if you use
  `--install-from-source` (`forward_ssh_agent: yes` in config.yml).

* For an `https://` repository, you can
  `export TPA_GIT_CREDENTIALS=username:token` in your environment
  before running `tpaexec deploy`.

## SSH key authentication

If you are cloning an SSH repository and have an SSH keypair
(`id_example` and `id_example.pub`), use SSH agent forwarding to
authenticate on the target instances:

* **You need to run `ssh-agent` locally**. If your desktop environment
  does not already set this up for you (as most do—`pgrep ssh-agent`
  to check if it's running), run `ssh-agent bash` to temporarily start
  a new shell with the agent enabled, and run `tpaexec deploy` from
  that shell.

* **Add the required key(s) to the agent** with
  `ssh-add /path/to/id_example` (the private key file)

* **Enable SSH agent forwarding** by setting `forward_ssh_agent: yes`
  at the top level in config.yml before `tpaexec provision`. (This is
  done by default if you use `--install-from-source`.)

During deployment, any keys you add to your agent will be made available
for authentication to remote servers through the forwarded agent
connection.

Use SSH agent forwarding with caution, preferably with a disposable
keypair generated specifically for this purpose. Users with the
privileges to access the agent's Unix domain socket on the target server
can co-opt the agent into impersonating you while authenticating to
other servers.

## HTTPS username/password authentication

If you are cloning an HTTPS repository with a username and
authentication token or password, just
`export TPA_GIT_CREDENTIALS=username:token` in your environment before
`tpaexec deploy`. During deployment, these credentials will be made
available to any `git clone` or `git pull` tasks (only). They will
not be written to disk on the target instances.

## Advice for 2ndQuadrant engineers

If you are cloning repositories from gitlab.2ndQuadrant.com:

1. Generate a read-only access token at
   [https://gitlab.2ndquadrant.com/profile/personal_access_tokens](https://gitlab.2ndquadrant.com/profile/personal_access_tokens)

2. Use this access token in `TPA_GIT_CREDENTIALS`. Do not use your
   2ndQuadrant username and password, nor any read/write access token
   that you use for your development work.

3. Treat the read-only access token as confidential information.
