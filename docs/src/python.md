---
description: The Python environment used by TPA and how to configure it.
---

# Python environment

TPA decides which Python interpreter to use based on the
[distribution it detects](distributions.md) on a target instance. It
will use Python 3 wherever possible, and fall back to Python 2 only when
unavoidable.

The `tpaexec configure` command will set `preferred_python_version`
according to the distribution.

Distribution| Python 2| Python 3
----|----|----
Debian 12/bookworm|✓|✓ (3.11)
Debian 11/bullseye|✓|✓ (3.9)
Debian 10/buster|✓|✓ (3.7)
Ubuntu 24.04/noble|✗|✓ (3.12)
Ubuntu 22.04/jammy|✗|✓ (3.10)
Ubuntu 20.04/focal|✗|✓ (3.8)
RHEL 10.x|✗|✓ (3.12)
RHEL 9.x|✗|✓ (3.9)
RHEL 8.x|✗|✓ (3.6)
RHEL 7.x|✓|✗ (3.6)
SLES 15|✗|✓ (3.6)


Ubuntu 20.04, 22.04, 24.04, RHEL 8.x, 9.x, 10.x, and SLES 15 can be used only with Python 3.

RHEL 7.x ships with Python 3.6, but the librpm bindings for system Python 3 are
not available.

You can decide for other distributions whether you prefer `python2` or
`python3`, but the default for new clusters is `python3`.

## Backwards compatibility

For compatibility with existing clusters, the default value of
`preferred_python_version` is `python2`, but you can explicitly choose
`python3` even on systems that were already deployed with `python2`.

```yaml
cluster_vars:
  preferred_python_version: python3
```

TPA will ignore this setting on distributions where it cannot use
Python 3.

## Python interpreter for installed scripts

TPA installs a small number of helper Python scripts on cluster nodes
(for example, `/etc/tpa/postgres-monitor`, which the deploy uses to
wait for Postgres to become available). The shebang line of each
installed script is templated from the `script_python_interpreter`
fact.

By default, `script_python_interpreter` is set to
`/usr/bin/env {{ python }}`, which means the script will run under
whichever `python3` binary `env` finds first on the node's `PATH` at
execution time. This matches TPA's historic behaviour and is the
right answer on most hosts: it picks up the system Python that TPA
itself targets for package installation.

If you need TPA's installed scripts to run under a specific Python
interpreter — for example, because you have multiple Python versions
on the host and want to remove ambiguity, or because you want to use
a non-system Python — set `script_python_interpreter` in
`cluster_vars` to the absolute path of the interpreter you want:

```yaml
cluster_vars:
  script_python_interpreter: /usr/bin/python3
```

Or, to point at a non-system Python:

```yaml
cluster_vars:
  script_python_interpreter: /opt/python3.11/bin/python3
```

The value is used verbatim after `#!` in the shebang line, so it must
be a path that the kernel can `exec` directly. If you set this
variable, ensure that the OS packages TPA installs to support its
scripts (for example `python3-psycopg2`) are available to that
interpreter — see the next section for how to influence which
packages TPA installs.

## Python version for installed packages

TPA installs several OS packages (RPMs or DEBs, depending on the
distribution) that provide Python modules its scripts depend on — for
example, `python3-psycopg2`. The name prefix used to construct these
package names is taken from the `python_pkg_prefix` fact, which
defaults to the distribution-detected Python (`python3` on every
currently-supported distribution other than RHEL 7).

If you want TPA to install packages for a non-default Python — for
example, because you have installed Python 3.11 alongside the system
Python and want TPA to depend on the matching `python311-psycopg2`
package rather than the default `python3-psycopg2` — set
`python_pkg_prefix` in `cluster_vars`:

```yaml
cluster_vars:
  python_pkg_prefix: python311
```

TPA will then construct package names using your prefix, installing
e.g. `python311-psycopg2`, `python311-barman`, and so on.

**Important:** `python_pkg_prefix` only controls *the names of the OS
packages TPA installs*. It does not by itself change which Python
interpreter TPA-installed scripts (such as `/etc/tpa/postgres-monitor`)
execute under. If you set `python_pkg_prefix` on a host that has more
than one Python interpreter installed, you almost certainly also want
to set `script_python_interpreter` (see the previous section) to the
absolute path of the matching interpreter. Otherwise the default
`/usr/bin/env`-based shebang on TPA's installed scripts may resolve
via `PATH` to a different Python than the one the
`python_pkg_prefix`-named packages were installed for, and imports
will fail at runtime.
