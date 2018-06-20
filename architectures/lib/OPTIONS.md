Common configuration options
============================

When you run ``tpaexec configure c --architecture a …``, you may append
any of the following options to the command (unless otherwise specified
by the documentation for the selected architecture).

Platform
--------

You may optionally specify ``--platform aws``. This is the default.

Any architecture may or may not support a particular platform. If not,
it will fail to configure the cluster.

The default is aws. The value is case-sensitive, and must correspond to
a supported platform according to ``tpaexec info platforms``.

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

Hostnames
---------

By default, ``tpaexec configure`` will randomly select as many hostnames
as it needs from a pre-approved list of several dozen names. This should
be enough for most clusters.

You may optionally specify ``--hostnames-from filename`` to select names
from a different list (e.g., if you need more names than are available
in the canned list). The file must contain one hostname per line.

If you specify ``--hostnames-from``, you may optionally also specify
``--hostnames-pattern '…pattern…'`` with an egrep-syntax pattern to
restrict hostnames to matching lines within the file. If you choose to
do this, you must ensure that the pattern matches only valid hostnames
(``[a-zA-Z0-9-]``) and finds a sufficient number thereof.
