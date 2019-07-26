(this file describes this architecture; for now we don't have a proper
PDF architecture document, since this architecture is very similar to
BDR-Always-ON)

Overview
========

The CAMO2x2 architecture can be described as identical to the
BDR-Always-ON architecture, except for two changes:

- You can optionally request that DELETE and TRUNCATE are replicated
  only to the other node in the same datacenter

- In the CAMO2x2 architecture, Commit At Most Once (CAMO) is always
  enabled, with each node being the CAMO partner of the other node in
  the same datacenter
