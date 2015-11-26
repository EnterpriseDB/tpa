This role defines a base PostgreSQL server - currently compiled from git.

To stop "make clean" from being performed, add postgres_make_clean to your
`--skip-tags`.

tags:

* postgres_make_clean: "make clean" before building
* postgres_install: installation phase, getting binaries in place
* postgres_initdb: create cluster
* postgres_start: start up the cluster
