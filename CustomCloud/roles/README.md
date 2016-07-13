CustomCloud roles
=================

This is an overview of the various roles available for CustomCloud.

common
------

The common role does the following:

1. Make sure Python is installed and usable.
2. Set up generic package repositories if required.
3. Install any generic packages if required.
4. Set the system hostname.

If fact collection is required, it should be performed separately in a
play that runs after the one that applies the common role.

Postgres
--------

The easiest way to install Postgres is from operating system packages.
The postgres/pkg role can be applied to any host to install the PGDG
packages for any supported distribution. Change pgversion to install
some other version than the default 9.4.

    roles:
      - role: 'postgres/pkg'
        pgversion: 9.3

The postgres/src and postgres/ext roles are provided to build and
install Postgres from source.

Both clone a git repository, checkout a particular ref, and build and
install from the resulting source tree. By default, the installation
lives in /opt/postgres/M.m/. Various knobs are provided to customise
configure and build flags.

    roles:
      - role: 'postgres/src'
        postgres_git_url: git://git.postgresql.org/git/postgresql.git
        postgres_git_ref: REL9_5_STABLE
        pgversion: 9.5

Once installed, the postgres/initdb and postgres/config roles can be
used to create a database cluster and configure it. On platforms where
the packages run initdb, the postgres/pkg role suppresses this behaviour
so that postgres/initdb can be used instead.

Postgres-XL
-----------

postgres-xl/pkg
postgres-xl/initall

Auxiliary software
------------------

barman
repmgr

System-level roles
------------------

sys/luks
sys/openvpn
sys/instance
