Training
========

This architecture is meant for internal use at 2ndQuadrant, and the
documentation references below are not accessible outside the company.

The process to request VMs for training is documented here:

    https://redmine.2ndquadrant.it/projects/courses/wiki/Virtual_Machines_for_training

This is the process to follow once a request has been received, e.g.,

    https://redmine.2ndquadrant.it/issues/10973

Cluster configuration
---------------------

Generate the cluster configuration by running the following command

```
tpaexec configure ~/clusters/training_10973 --architecture training \
  --redmine-id 10973 --instances 15 \
  --distribution Debian --minimal \
  --platform aws --region eu-west-1 --subnet 10.33.115.0/24
```

You must specify ``--architecture training``.

You must specify ``--redmine-id <number>`` corresponding to the ticket
number in Redmine.

You must specify ``--instances <number>`` corresponding to the number of
instances required.

You may optionally specify ``--region eu-west-1``. This is the default
region, but you may use any existing AWS region that you have access to
(and that will permit the required number of instances to be created).

You may optionally specify ``--subnet 10.33.115.0/24``. This is the
default value, but you SHOULD change it if multiple clusters will be
provisioned at the same time.

You may also specify any of the options described by
``tpaexec help configure-options``.

Provisioning and deployment
---------------------------

Provision the cluster:

```
tpaexec provision ~/clusters/training_10973
```

(We assume that the necessary AWS credentials are available. See
``tpaexec help platforms/aws`` for more details.)

If you specified ``--minimal`` when generating the cluster above, you do
not need to run the deployment at all. Otherwise, run

```
tpaexec deploy ~/clusters/training_10973
```
