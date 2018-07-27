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

Training
  Clusters for 2ndQuadrant training sessions

Images
  Clusters to generate AMIs with preinstalled packages

Run ``tpaexec info architectures/M1`` (or any of the architecture names
listed above) for more information.
