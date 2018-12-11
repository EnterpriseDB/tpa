(this file temporarily describes this architecture until we have a
proper PDF architecture document)

Overview
========

The CAMO2x2 architecture can be described as identical to the
BDR-Always-ON architecture, except for three changes:

- The addition of a *reporting node* in Datacenter 1, which is a
  *logical standby* node;

- DELETE and TRUNCATE are replicated only to the other node in the
  same datacenter.

- In the CAMO2x2 architecture, Commit At Most Once (CAMO) is always
  enabled, with each node being the CAMO partner of the other node in
  the same datacenter.
