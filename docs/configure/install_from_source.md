# Installing from source

You can define a list of extensions to build and install from their Git
repositories by setting ``install_from_source`` in config.yml:

```yaml
cluster_vars:
  install_from_source:
    - name: ext
      git_repository_url: https://repo.example.com/ext.git
      git_repository_ref: dev/example

    - name: otherext
      git_repository_url: ssh://repo.example.com/otherext.git
      git_repository_ref: master
      source_directory: /opt/postgres/src/otherext
      build_directory: /opt/postgres/build/otherext
      build_commands:
        - "make -f /opt/postgres/src/otherext/Makefile install"
      build_environment:
        VAR: value
```

TPAexec will build and install extensions one by one in the order
listed, so you can build extensions that depend on another (such as
pglogical and BDR) by mentioning them in the correct order.

Each entry must specify a ``name``, ``git_repository_url``, and
``git_repository_ref`` (default: ``master``) to build. If the repository
requires authentication, you can use
[SSH agent forwarding or an HTTPS username/password](postgres.md#git-credentials).
You can also set the ``source_directory``, ``build_directory``,
``build_commands``, and ``build_environment`` as shown above.

Run ``tpaexec deploy … --skip-tags build-clean`` in order to reuse the
build directory when doing repeated deploys. (Otherwise the old build
directory is emptied before starting the build.)

Whenever you run a source build, Postgres will be restarted.
