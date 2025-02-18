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
Ubuntu 24.04/jammy|✗|✓ (3.12)
Ubuntu 22.04/jammy|✗|✓ (3.10)
Ubuntu 20.04/focal|✗|✓ (3.8)
RHEL 9.x|✗|✓ (3.9)
RHEL 8.x|✗|✓ (3.6)
RHEL 7.x|✓|✗ (3.6)


Ubuntu 20.04, 22.04 and RHEL 8.x can be used only with Python 3.

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
