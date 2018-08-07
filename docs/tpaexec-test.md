tpaexec test
============

Now we run architecture-specific tests against a deployed cluster to
verify the installation. At the end of this stage, we have a
fully-functioning cluster.

You must have already run ``tpaexec configure``, ``tpaexec provision``,
and ``tpaexec deploy`` successfully before you can run ``tpaexec test``.

## Quickstart

```bash
[tpa]$ tpaexec test ~/clusters/speedy -v
```

Output is once again logged to ``ansible.log`` in the cluster directory.

If this command succeeds, your cluster works.

Congratulations.
