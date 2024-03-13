# Postgres source installation

If you set `postgres_installation_method` to `src`, TPA compiles and 
installs Postgres from source. This feature is meant for use
in development and testing and allows you to switch between packaged
and source builds in an identically configured cluster.

You don't need to change the defaults, which gives you a
working cluster with debugging enabled.

## Git repository

The default settings build and install Postgres from the community
Git repository, using the `REL_xx_STABLE` branch corresponding to your
`postgres_version`. You can specify a different repository or branch
(any valid git reference) as follows:

```yaml
cluster_vars:
  postgres_git_url: git://git.postgresql.org/git/postgresql.git
  postgres_git_ref: REL_12_STABLE
```

The default `git.postgresql.org` repository doesn't require
authentication. But, if necessary, you can use
[SSH agent forwarding or an HTTPS username/password](git-credentials.md)
to authenticate to other repositories.

If the directory already exists (for example, if you're redeploying),
the repository is cloned into `postgres_src_dir` (default:
`/opt/postgres/src/postgres`) or updated with `git pull`.

### Build customization

By default, TPA configures and builds Postgres with debugging
enabled and sensible defaults in `postgres_build_dir` (default:
`/opt/postgres/build/postgres`). You can change various settings to
customize the build:

```yaml
cluster_vars:
  postgres_extra_configure_env:
    CFLAGS: "-O3"
  postgres_extra_configure_opts:
    - --with-llvm
    - --disable-tap-tests
```

This example runs `./configure` with the options in
`postgres_extra_configure_opts` and the settings from
`postgres_extra_configure_env` defined in the environment. Some
options are specified by default (for example, `--with-debug`) but can be
negated by the corresponding `--disable-xxx` or `--without-xxx`
options. Building `--without-openssl` isn't supported.

If required, you can also change the following default build commands:

```yaml
cluster_vars:
  postgres_make_command: "make -s"
  postgres_build_targets:
    - "all"
    - "-C contrib all"
  postgres_install_targets:
    - "install"
    - "-C contrib install"
```

To reuse the build directory when doing repeated deploys,
run `tpaexec deploy … --skip-tags build-clean`. Otherwise the old build
directory is emptied before starting the build. You can also configure
[local source directories](configure-source.md#local-source-directories)
to speed up your development builds.

Whenever you run a source build, Postgres restarts.

## Additional components

Even if you install Postgres from packages, you can compile and install
extensions from source. See
[`install_from_source`](install_from_source.md) to learn how to install and configure from source.

If you install Postgres from source, however, you will need to install
extensions from source as well because the extension packages typically
depend on the Postgres packages being installed.

## Package installation

For package installation, see
[installing Postgres and Postgres-related packages](postgres_installation_method_pkg.md)
with `postgres_installation_method: pkg` (the default).
