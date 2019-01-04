# Common configuration options

When you run ``tpaexec configure c --architecture a …``, you may append
any of the following options to the command (unless otherwise specified
by the documentation for the selected architecture).

## Owner

Every cluster must be directly traceable to a person responsible for the
provisioned resources.

By default, a cluster will be tagged as being owned by the login name of
the user running ``tpaexec provision``. If this name does not identify a
person (e.g., postgres, ec2-user), you must specify ``--owner SomeId``
to set an identifiable owner.

(You may use your initials, or ``"Firstname Lastname"``, or anything
else that identifies you uniquely.)

## Platform options

You may optionally specify ``--platform aws``. This is the default.

Any architecture may or may not support a particular platform. If not,
it will fail to configure the cluster.

The default is aws. The value is case-sensitive, and must correspond to
a supported platform according to ``tpaexec info platforms``.

You may optionally specify ``--region eu-west-1``. This is the default
region, but you may use any existing AWS region that you have access to
(and that will permit the required number of instances to be created).

You may optionally specify ``--instance-type t3.micro`` (the default) or
any other valid instance type for the selected platform.

### Subnet selection

By default, each cluster is assigned a random /28 subnet under 10.33/16,
but depending on the architecture, there may be one or more subnets, and
each subnet may be anywhere between a /24 and a /29.

You may specify ``--subnet 192.0.2.128/27`` to use a particular subnet.

You may instead specify ``--subnet-pattern 192.0.x.x`` to generate
random subnets (as many as required by the architecture) matching the
given pattern.

## Disk space

You may optionally specify ``--root-volume-size 64`` to set the size of
the root volume in GB. The default is 16GB. (Depending on the image used
to create instances, there may be a minimum size for the root volume.)

For architectures that support separate postgres and barman volumes:

You may optionally specify ``--postgres-volume-size 64`` to set the size
of the Postgres volume in GB. The default is 16GB.

You may optionally specify ``--barman-volume-size 64`` to set the size
of the Barman volume in GB. The default is 32GB.

## Distribution

You may optionally specify ``--distribution <label>`` to specify the OS
to be used on the cluster's instances. The value is case-sensitive.

The selected platform determines which distributions are available, and
which one is used by default. For more details, see
``tpaexec info platforms/<platformname>``.

In general, you should be able to use "Debian", "RedHat", and "Ubuntu"
to select TPA images that have Postgres and other software preinstalled
(to reduce deployment times). To use stock distribution images instead,
append "-minimal" to the label, e.g., "Debian-minimal".

For brevity, you can also use ``--os`` instead of ``--distribution``.

This option is not meaningful for the "bare" platform, where TPAexec has
no control over what distribution is installed.

## 2ndQuadrant repositories

By default, we install the 2ndQuadrant public repository and add on any
product repositories that the architecture requires.

You may optionally specify ``--2Q-repositories source/name/maturity …``
to specify the complete list of 2ndQuadrant repositories to install on
each instance in addition to the 2ndQuadrant public repository.

If you do this, you must first ``export TPA_2Q_SUBSCRIPTION_TOKEN=xxx``
before you run tpaexec. You can get a subscription token from the
2ndQuadrant Portal (Support → Software subscriptions → Add).

## Software versions

You may optionally specify ``--postgres-version 10`` (the default) or
any other major version of Postgres (e.g., 9.6). TPA supports Postgres
9.4 and above. Postgres 9.4 and 9.5 were known to work at one time, but
are no longer actively maintained.

By default, we always install the latest version of every package. This
is usually the desired behaviour, but in some testing scenarios, it may
be necessary to select specific package versions using the following
options:

1. ``--postgres-package-version 10.4-2.pgdg90+1``
2. ``--repmgr-package-version 4.0.5-1.pgdg90+1``
3. ``--barman-package-version 2.4-1.pgdg90+1``
4. ``--pglogical-package-version '2.2.0*'``
5. ``--bdr-package-version '3.0.2*'``
5. ``--pgbouncer-package-version '1.8*'``

You may also specify ``--extra-packages p1 p2 …`` or
``--extra-postgres-packages p1 p2 …`` to install additional packages.
The former lists packages to install along with system packages, while
the latter lists packages to install later along with postgres packages.
(If you mention packages that depend on Postgres in the former list, the
installation will fail because Postgres will not yet be installed.) The
arguments are passed on to the package manager for installation without
any modifications.

The ``--extra-optional-packages p1 p2 …`` option behaves like
``--extra-packages``, but it is not an error if the named packages
cannot be installed.

## Hostnames

By default, ``tpaexec configure`` will randomly select as many hostnames
as it needs from a pre-approved list of several dozen names. This should
be enough for most clusters.

You may optionally specify ``--hostnames-from filename`` to select names
from a different list (e.g., if you need more names than are available
in the canned list). The file must contain one hostname per line.

You may optionally specify ``--hostnames-pattern '…pattern…'`` to
restrict hostnames to those matching the egrep-syntax pattern. If you
choose to do this, you must ensure that the pattern matches only valid
hostnames (``[a-zA-Z0-9-]``) and finds a sufficient number thereof.

## Locations

By default, ``tpaexec configure`` will use the names ``first``,
``second``, and so on for any locations used by the selected
architecture. Some architectures may specify different defaults, e.g.,
``main`` and ``dr`` for M1.

You may optionally specify ``--location-names N1 N2 …`` to provide more
meaningful names for each location.
