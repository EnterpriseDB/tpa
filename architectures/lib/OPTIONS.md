Common configuration options
============================

When you run ``tpaexec configure c --architecture a …``, you may append
any of the following options to the command (unless otherwise specified
by the documentation for the selected architecture).

Platform options
----------------

You may optionally specify ``--platform aws``. This is the default.

Any architecture may or may not support a particular platform. If not,
it will fail to configure the cluster.

The default is aws. The value is case-sensitive, and must correspond to
a supported platform according to ``tpaexec info platforms``.

You may optionally specify ``--region eu-west-1``. This is the default
region, but you may use any existing AWS region that you have access to
(and that will permit the required number of instances to be created).

You should specify ``--subnet 10.33.115.0/24`` to select the subnet used
for the cluster.

You may optionally specify ``--instance-type t2.micro`` (the default) or
any other valid instance type for the selected platform.

Distribution
------------

You may optionally specify ``--distribution Debian`` (or RedHat, or
Ubuntu).

You may optionally specify ``--minimal`` if you want to use the stock
distribution images instead of TPA images that have Postgres and other
software preinstalled.

For brevity, you can also use ``--os Debian-minimal``.

The default is Debian. The value is case-sensitive, and must correspond
to a supported distribution according to ``tpaexec info distributions``.

Software versions
-----------------

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

Hostnames
---------

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
