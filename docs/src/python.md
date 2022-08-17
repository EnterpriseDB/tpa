# Python environment

TPAexec decides which Python interpreter to use based on the
[distribution it detects](distributions.md) on a target instance. It
will use Python 3 wherever possible, and fall back to Python 2 only when
unavoidable.

The `tpaexec configure` command will set `preferred_python_version`
according to the distribution.

Distribution| Python 2| Python 3
----|----|----
Debian 10/buster|✓|✓ (3.7)
Debian 9/stretch|✓|✓ (3.5)
Debian 8/jessie|✓|✗ (3.4)
Ubuntu 16.04/xenial|✓|✓ (3.5)
Ubuntu 18.04/bionic|✓|✓ (3.6)
Ubuntu 20.04/focal|✗|✓ (3.8)
Ubuntu 22.04/jammy|✗|✓ (3.10)
RHEL 7.x|✓|✗ (3.6)
RHEL 8.x|✗|✓ (3.6)

Ubuntu 20.04, 22.04 and RHEL 8.x can be used only with Python 3.

RHEL 7.x ships with Python 3.6, but the librpm bindings for Python 3 are
not available, so TPAexec must use Python 2 instead. Debian 8 does not
have the Python 3.5+ required to support Ansible.

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

TPAexec will ignore this setting on distributions where it cannot use
Python 3.
