# Installing from source

You can define a list of extensions to build and install from their Git
repositories by setting `install_from_source` in config.yml:

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

Each entry must specify a `name`, `git_repository_url`, and
`git_repository_ref` (default: `master`) to build. You can use
[SSH agent forwarding or an HTTPS username/password](git-credentials.md)
to authenticate to the Git repository; and also set
`source_directory`, `build_directory`, `build_environment`, and
`build_commands` as shown above.

Run `tpaexec deploy … --skip-tags build-clean` in order to reuse the
build directory when doing repeated deploys. (Otherwise the old build
directory is emptied before starting the build.) You can also configure
[local source directories](configure-source.md#local-source-directories)
to speed up your development builds.

Whenever you run a source build, Postgres will be restarted.

## Build dependencies

If you're building from source, TPAexec will ensure that the basic
Postgres build dependencies are installed. If you need any additional
packages, mention them in [`packages`](packages.md). For example

```yaml
cluster_vars:
  packages:
    common:
    - golang-1.16
```
