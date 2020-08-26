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
$ tpaexec configure ~/clusters/speedy -a BDR-Simple             \
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
    --architecture BDR-Simple --platform docker                 \
    --install-from-source 2ndqpostgres:2QREL_11_STABLE_3_6      \
      pglogical3 bdr3                                           \
    --local-source-directories                                  \
      pglogical3:~/src/pglogical bdr3:~/src/bdr
```

Read on for a detailed explanation of how to build Postgres, pglogical,
BDR, and other components with custom locations and build parameters.

## Configuration

There are two aspects to configuring source builds.

If you just want a cluster running a particular combination of sources,
run ``tpaexec configure`` to generate a configuration with sensible
defaults to download, compile, and install the components you select.
You can build Postgres or 2ndQPostgres, pglogical, and BDR, and specify
branch names to build from, as shown in the examples above. The
available options are documented below.

The underlying mechanism is capable of much more than the command-line
options allow. By editing config.yml, you can clone different source
repositories, change the build location, specify different configure or
build parameters, redefine the build commands entirely, and so on. You
can, therefore, build things other than Postgres, pglogical, and BDR.
