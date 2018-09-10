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
tpaexec configure ~/clusters/training_10973 --architecture Training \
  --redmine-id 10973 --instances 15 \
  --platform aws --region eu-west-1 \
  --distribution Debian-minimal
```

You must specify ``--architecture training``.

You must specify ``--redmine-id <number>`` corresponding to the ticket
number in Redmine.

You must specify ``--instances <number>`` corresponding to the number of
instances required.

You may also specify any of the options described by
``tpaexec help configure-options``.

This architecture does not use separate postgres volumes, so you cannot
use the ``--postgres-volume-size`` or ``--barman-volume-size`` options.

Provisioning and deployment
---------------------------

Provision the cluster:

```
tpaexec provision ~/clusters/training_10973
```

(We assume that the necessary AWS credentials are available. See
``tpaexec help platforms/aws`` for more details.)

If you specified ``Debian-minimal`` when generating the cluster above,
you do not need to run the deployment at all. Otherwise, run

```
tpaexec deploy ~/clusters/training_10973
```
