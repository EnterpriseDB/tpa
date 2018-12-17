Architectures
=============

An architecture is a recommended layout of servers and software to set
up Postgres for a specific purpose.

Select one of the following architectures, and ``tpaexec configure``
will generate the cluster configuration for you.

M1
  Postgres with streaming replication (one primary, n replicas)

BDR-Simple
  BDR with no frills on n nodes (good for experiments)

BDR-Always-ON
  BDR in an Always-ON configuration

CAMO2x2
  A BDR-Always-ON variant with two nodes configured as CAMO ("commit at
  most once") partners in each of two separate locations

Training
  Clusters for 2ndQuadrant training sessions

Images
  Clusters to generate distribution images with preinstalled packages

Run ``tpaexec info architectures/M1`` (or any of the architecture names
listed above) for more information.

Run ``tpaexec configure --architecture M1 --help`` to see the available
configure options for the architecture.
