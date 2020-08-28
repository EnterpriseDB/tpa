# Configuring Postgres

This page documents various Postgres-related configuration settings.

The variables described here can be set for the entire cluster in
``cluster_vars``, or set or overriden for a specific instance in
``vars``, so you can build a cluster with different versions and
configurations of Postgres across instances.

## Version

Set ``postgres_version`` in config.yml or use the
[``--postgres-version`` configure option](../tpaexec-configure.md#software-versions)
to specify which Postgres major version you want to install (e.g., 12,
11, 9.6).

## Package installation

Set ``postgres_installation_method: pkg`` to install Postgres from
packages (the default). There is a separate page on how to
[install Postgres and Postgres-related packages](postgres_packages.md).

## Source installation

Set ``postgres_installation_method: src`` to build and install Postgres
from the community Git repository, using the ``REL_xx_STABLE`` branch
corresponding to your ``postgres_version``. You can specify a different
repository or branch (any valid git reference) as follows:

```yaml
cluster_vars:
  postgres_git_url: git://git.postgresql.org/git/postgresql.git
  postgres_git_ref: REL_12_STABLE
```

The repository will be cloned into ``postgres_src_dir`` (default:
``/opt/postgres/src/postgres``), or updated with ``git pull`` if the
directory already exists (e.g., if you are re-deploying).

### Git credentials

If the repository you want to clone requires authentication, you have
two options to authenticate without writing the credentials to disk on
the target instance:

* For an ``ssh://`` repository, you can add an SSH key to your local
  ssh-agent. Agent forwarding is enabled by default if you use
  ``--install-from-source`` (``forward_ssh_agent: yes`` in config.yml).

* For an ``https://`` repository, you can
  ``export TPA_GIT_CREDENTIALS=username:password`` in your environment
  before running ``tpaexec deploy``.

### Build customisation

By default, TPAexec will configure and build Postgres with debugging
enabled and sensible defaults in ``postgres_build_dir`` (default:
``/opt/postgres/build/postgres``). You can change various settings to
customise the build:

```yaml
cluster_vars:
  postgres_extra_configure_env:
    CFLAGS: "-O3"
  postgres_extra_configure_opts:
    - --with-llvm
    - --disable-tap-tests
```

This will run ``./configure`` with the options in
``postgres_extra_configure_opts`` and the settings from
``postgres_extra_configure_env`` defined in the environment. Some
options are specified by default (e.g., ``--with-debug``), but can be
negated by the corresponding ``--disable-xxx`` or ``--without-xxx``
options. Building ``--without-openssl`` is not supported.

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

Run ``tpaexec deploy … --skip-tags build-clean`` in order to reuse the
build directory when doing repeated deploys. (Otherwise the old build
directory is emptied before starting the build.)

Whenever you run a source build, Postgres will be restarted.

## Additional components

Even if you install Postgres from packages, you can compile and install
extensions from source. There's a separate page about how to configure
[``install_from_source``](install_from_source.md).

If you install Postgres from source, however, you will need to install
extensions from source as well, because the extension packages typically
depend on the Postgres package(s) being installed.

## Post-installation

* [Create users](postgres_users.md)

* [Create databases](postgres_databases.md)
