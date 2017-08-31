TPA roles
=========

This is an overview of the various roles available for TPA.

common
------

This role should be included first in every deployment playbook. It does
the following things:

1. Determines and sets ansible_distribution/ansible_os_family/etc. This
   is a lightweight alternative to fact discovery via the setup module.
2. Makes sure Python is installed and usable, and installs any other
   generic packages required (e.g., strace).
3. Sets the system hostname and installs /etc/hosts and
   /etc/ssh/known_hosts for every host in the cluster.

If fact collection is required, it should be performed separately in a
play that runs after the one that applies the common role.

Postgres
--------

The easiest way to install Postgres is from operating system packages.
The postgres/pkg role can be applied to any host to install the PGDG
packages for any supported distribution. Change postgres_version to
install some other version than the default 9.6.

    roles:
      - role: 'postgres/pkg'
        postgres_version: 9.4

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
        postgres_version: 9.5

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
