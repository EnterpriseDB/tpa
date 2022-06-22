# Building from source

TPAexec can build Postgres and other required components from source and
deploy a cluster with exactly the same configuration as with the default
packaged installation. This makes it possible to deploy repeatedly from
source to quickly test changes in a realistic, fully-configured cluster
that reproduces every aspect of a particular setup, regardless of
architecture or platform.

You can even combine packaged installations of certain components with
source builds of others. For example, you can install Postgres from
packages and compile pglogical and BDR from source, but package
dependencies would prevent installing pglogical from source and BDR from
packages.

Source builds are meant for use in development, testing, and for support
operations.

## Quickstart

Spin up a cluster with 2ndQPostgres and pglogical3 built from the stable
3.6 branches, with BDR3 built from a development branch:

```bash
$ tpaexec configure ~/clusters/speedy -a BDR-Always-ON          \
    --layout bronze                                             \
    --install-from-source                                       \
      2ndqpostgres:2QREL_11_STABLE_3_6                          \
      pglogical3:REL3_6_STABLE                                  \
      bdr3:dev/RM12345-feature
```

As above, but set up a cluster that builds 2ndQPostgres source code from
the official git repository and uses the given local work trees to build
pglogical and BDR. This feature is specific to Docker:

```bash
$ tpaexec configure ~/clusters/speedy                           \
    --architecture BDR-Always-ON --layout bronze                \
    --platform docker                                           \
    --install-from-source 2ndqpostgres:2QREL_11_STABLE_3_6      \
      pglogical3 bdr3                                           \
    --local-source-directories                                  \
      pglogical3:~/src/pglogical bdr3:~/src/bdr
```

After deploying your cluster, you can use
`tpaexec deploy … --skip-tags build-clean` on subsequent runs to
reuse build directories. (Otherwise the build directory is emptied
before starting the build.)

Read on for a detailed explanation of how to build Postgres, pglogical,
BDR, and other components with custom locations and build parameters.

## Configuration

There are two aspects to configuring source builds.

If you just want a cluster running a particular combination of sources,
run `tpaexec configure` to generate a configuration with sensible
defaults to download, compile, and install the components you select.
You can build Postgres or Postgres Extended, pglogical, and BDR, and specify
branch names to build from, as shown in the examples above.

The underlying mechanism is capable of much more than the command-line
options allow. By editing config.yml, you can clone different source
repositories, change the build location, specify different configure or
build parameters, redefine the build commands entirely, and so on. You
can, therefore, build things other than Postgres, pglogical, and BDR.

The available options are documented here:

* [Building Postgres from source](postgres_installation_method_src.md)

* [Building extensions with `install_from_source`](install_from_source.md)

## Local source directories

You can use TPAexec to provision Docker containers that build Postgres
and/or extensions from your local source directories instead of from a
Git repository.

Suppose you're using `--install-from-source` to declare what you want
to build:

```bash
$ tpaexec configure ~/clusters/speedy                           \
    --architecture BDR-Always-ON --layout bronze                \
    --platform docker                                           \
    --install-from-source 2ndqpostgres:2QREL_11_STABLE_3_6      \
      pglogical3:REL3_6_STABLE bdr3:REL3_6_STABLE               \
      …
```

By default, this will clone the known repositories for Postgres Extended,
pglogical3, and bdr3, check out the given branches, and build them. But
you can add `--local-source-directories` to specify that you want the
sources to be taken directly from your host machine instead:

```bash
$ tpaexec configure ~/clusters/speedy                           \
    --architecture BDR-Always-ON --layout bronze                \
    --platform docker                                           \
    --install-from-source 2ndqpostgres:2QREL_11_STABLE_3_6      \
      pglogical3 bdr3                                           \
    --local-source-directories                                  \
      pglogical3:~/src/pglogical bdr3:~/src/bdr                 \
    …
```

This configuration will still install Postgres Extended from the repository,
but it obtains pglogical3 and bdr3 sources from the given directories on
the host. These directories are bind-mounted read-only into the Docker
containers at the same locations where the git repository would have
been cloned to, and the default (out-of-tree) build proceeds as usual.

If you specify a local source directory for a component, you cannot
specify a branch to build (cf. `pglogical3:REL3_6_STABLE` vs.
`pglogical3` for `--install-from-source` in the examples above). The
source directory is mounted read-only in the containers, so TPAexec
cannot do anything to change it—neither `git pull`, nor
`git checkout`. You get whichever branch you have checked out locally,
uncommitted changes and all.

Using `--local-source-directories` includes a list of Docker volume
definitions in config.yml:

```yaml
local_source_directories:
  - /home/ams/src/pglogical:/opt/postgres/src/pglogical:ro
  - /home/ams/src/bdr:/opt/postgres/src/bdr:ro
  - ccache-bdr_src_36-20200828200021:/root/.ccache:rw
```

### ccache

TPAexec installs ccache by default for source builds of all kinds. When
you are using a Docker cluster with local source directories, by default
a new Docker volume is attached to the cluster's containers to serve as
a shared ccache directory. This volume is completely isolated from the
host, and is removed when the cluster is deprovisioned.

Use the `--shared-ccache /path/to/host/ccache` configure option to
specify a longer-lived shared ccache directory. This directory will be
bind-mounted r/w into the containers, and its contents will be shared
between the host and the containers.

(By design, there is no way to install binaries compiled on the host
directly into the containers.)
