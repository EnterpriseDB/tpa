# Git credentials

You can clone Git repositories that require
authentication. If you're
[installing Postgres from source](postgres_installation_method_src.md) or
[using `install_from_source`](install_from_source.md) to compile and
install extensions, and the source repositories require authentication, 
you can use SSH key-based authentication or HTTPS username/password based 
authentication to access them with TPA.

You have two options to authenticate without writing the credentials to
disk on the target instance:

* For an `ssh://` repository, you can add an SSH key to your local
  SSH agent. Agent forwarding is enabled by default if you use
  `--install-from-source` (`forward_ssh_agent: yes` in `config.yml`).

* For an `https://` repository, you can
  `export TPA_GIT_CREDENTIALS=username:token` in your environment
  before running `tpaexec deploy`.

!!! Note
    Docker containers on macOS can't use ssh:// URLs because SSH access from 
    the host to containers doesn't work. https:// repository URLs will work fine.

## SSH key authentication

If you're cloning an SSH repository and have an SSH key pair
(`id_example` and `id_example.pub`), use SSH agent forwarding to
authenticate on the target instances:

* **You need to run `ssh-agent` locally**. If your desktop environment
  doesn't already set this up for you (as most do: `pgrep ssh-agent`
  to check if it's running), run `ssh-agent bash` to temporarily start
  a new shell with the agent enabled. Then run `tpaexec deploy` from
  that shell.

* **Add the required key(s) to the agent** with
  `ssh-add /path/to/id_example` (the private key file).

* **Enable SSH agent forwarding** by setting `forward_ssh_agent: yes`
  at the top level in `config.yml` before `tpaexec provision`. (This is
  done by default if you use `--install-from-source`.)

During deployment, any keys you add to your agent are made available
for authentication to remote servers through the forwarded agent
connection.

Use SSH agent forwarding with caution, preferably with a disposable
key pair generated specifically for this purpose. Users with the
privileges to access the agent's Unix domain socket on the target server
can co-opt the agent into impersonating you while authenticating to
other servers.

## HTTPS username/password authentication

If you're cloning an HTTPS repository with a username and
authentication token or password, just
`export TPA_GIT_CREDENTIALS=username:token` in your environment before
`tpaexec deploy`. During deployment, these credentials are made
available to any `git clone` or `git pull` tasks (only). They aren't
written to disk on the target instances.
