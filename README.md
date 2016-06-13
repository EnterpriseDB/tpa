# TPA
2ndQuadrant Trusted PostgreSQL Architecture

© Copyright 2ndQuadrant, 2016

Confidential property of 2ndQuadrant; not for public release.

TPA defines a trusted architecture for a fully configureed PostgreSQL cluster.
TPA also allows you to deploy that architecture in minutes using industry standard
configuration management tools.

TPA uses a library called CustomCloud to Provision and Deploy clusters.
Installing that software is discussed here: [CustomCloud README](CustomCloud/README.md)

TPA "creates a PostgreSQL cluster". TPA is designed to install complex configurations,
including basic Streaming Replication clusters, BDR super-clusters and massively
parallel clusters.
If you just want a basic Streaming Replication cluster, click here
[CustomCloud/clusters/test/tpa/README](CustomCloud/clusters/test/tpa/README.md)
to find out how to get a cluster with 1 Master and 2 standby replicas.

Clusters can be put together in complex ways, so to understand exactly what you'll get, lets look at the structure
of a PostgreSQL cluster and introduce some new terms for the various parts. 

Custom Cloud creates a new “cluster” as a ClusterGroup.
A ClusterGroup contains at least one Cluster; a basic Cluster consists of a Cluster with 1 Master and 1 or more replica nodes.
Actions at ClusterGroup level are therefore
* Create ClusterGroup
* Remove ClusterGroup

(Each ClusterGroup has 1 or more Clusters)
Clusters have these actions
* Add Cluster (to ClusterGroup)
* Remove Cluster (from ClusterGroup)
* Switchover - move Master to another node, as a manual action
* Add replica node
* Remove replica node

(Each Cluster has 1 or more Nodes. Nodes are also known as Instances)
Each Node has these actions
* Detach replica (“fork”)
* Resize instance

TPA June implements these actions
* Add ClusterGroup consisting of 1 Master and 2 standby replicas.
Link [CustomCloud/clusters/test/tpa/README](CustomCloud/clusters/test/tpa/README.md)
* Remove ClusterGroup

TPA July implements most of the remaining actions.


Pre-amble
=========
2ndQuadrant acknowledges that there are a lot customers/users out there who
will be moving towards (or are already) using PostgreSQL. Many of these
customers not just want to use Postgres but they also want to setup
replication, they worry about backup and monitoring and all related aspects.
Besides Postgres, there’s the associated ecosystem: barman, repmgr, etc. So
which version of these would go along with their Postgres install, how and what
to do for minor/major upgrades worries them. Even decisions about which Linux
distro/flavor to use in their deployments; it starts from there. And now with
the cloud options and compliances become more stringent, things are becoming
more confusing.

While that provides 2ndQuadrant with Services opportunities in the short term,
2ndQuadrant would like to strive towards providing a best-practices based
integrated architecture approach for the longer term. Following are the broad
overarching goals in this endeavor of 2ndQuadrant Trusted PostgreSQL
Architecture (TPA). It is basically going to draw on the years of experience
that 2ndQuadrant has had while serving the community and customer base:

I got what TPA is, how do I Get Started?
========================================
Click on [CustomCloud README](CustomCloud/README.md) to get started with
installing Ansible, Python and other components.

Click on [CustomCloud/clusters/test/tpa/README](CustomCloud/clusters/test/tpa/README.md)
to create your own TPA cluster in minutes!

Or read below for more on TPA.

Binaries for all components
===========================
We need to come up with a list of binaries that are going to be deployed.
Different components will have different versions compatible with each other. A
list of such compatible versions which make up a usable stack needs to be
maintained and tracked.

Best Practice: Integrated Architecture
======================================
With all the binaries identified, we need to come up with an integrated
architecture which deploys the components using the best possible
configuration. One way could be to come up configuration templates for each
component for a specific version. The other way is to dynamically fill up
proper configuration parameters as we go along the deployment.  Deployment of
additional components (contrib modules, etc) needs to be handled seamlessly.
Minor version upgrades need to be handled seamlessly.

Deployment on Cloud/On-Premise/Hybrid
======================================
TPA needs to be agnostic of the deployment environment and topology. TPA needs
to be “cloud agnostic” eventually.

Integrated, Secure
==================
Ensuring that all the components have proper security levels enabled at each
layer is required. The deployment instances also need to have proper security
parameters in place. Only those instances which need to be publicly visible,
need to be. Rest need to be inside private subnets and security groups and so
on.

Integrated, Tested
==================
Testing of the entire integrated stack is going to be very important. Starting
with testing of individual components, there have to be automated test suites
which test out the entire stack inter-working of various components.

Integrated, Performance
=======================
Performance of each individual component needs to be verifiable to ensure that
the deployment is at its optimal best and making proper use of the resources
allocated to it.  Performance of the entire stack also needs to be vetted out
because individual components might perform ok stand-alone but might not work
that great as part of an entire stack.

Integrated, Logging and Monitoring
==================================
A mechanism needs to be in place to monitor all the components.  Logging of
individual components will be needed to do troubleshooting and forensics in
case of debugging requirements.

Pricing
=======
Both 2ndQuadrant and the customer need to be able to look at pricing and be
able to drill down into individual component billing details.

Usability – new management UIs
==============================
A web UI to actually provision the components, see what’s been provisioned,
drill down into the details of each component (including pricing) with
configurations of each deployment saved in a proper JSON format and version
controlled is going to be absolutely critical

Documentation
=============
The documentation around TPA and various support components and platforms and
the UI needs to be top-notch and always kept up-to-date across various releases

Certification
=============
This initiative should be certified for usage by Governments, Health IT and
Finance Tech firms. Certifications like PCI-DSS, HIPAA, ISO 27001 etc. will be
necessary to gain the trust and confidence of uses cases in the compulsory
compliance domains.

Get Started
===========
Click on [CustomCloud README](CustomCloud/README.md) to get started with
installing Ansible, Python and other components.

Click on [CustomCloud/clusters/test/tpa/README](CustomCloud/clusters/test/tpa/README.md)
to create your own TPA cluster in minutes!
