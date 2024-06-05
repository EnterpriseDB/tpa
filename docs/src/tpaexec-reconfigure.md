---
description: The command that reads config.yml, changes the cluster in various ways and outputs a new config.yml. 
---

# tpaexec reconfigure

The `tpaexec reconfigure` command reads config.yml and generates a
revised version of it that changes the cluster in various ways according
to its arguments.

## Arguments

As with other tpaexec commands, the cluster directory must always be
given.

## Changing a cluster's architecture

The following arguments enable the cluster's architecture to be changed:

- `--architecture <architecture>`(required)<br>
The new architecture for the cluster. At present the only supported
architecture is `PGD-Always-ON`

- `--pgd-proxy-routing <global|local>`(required)<br>
How PGD-Proxy is to route connections. See
[the PGD-Always-ON documentation](architecture-PGD-Always-ON.md) for more
information about the meaning of this argument.

- `--edb-repositories <repositories>`(optional)<br>
A space-separated list of EDB package repositories. It is usually
unnecessary to specify this; `tpaexec configure` will choose a suitable
repository based on the postgres flavour in use in the cluster.

After changing the architecture, run [tpaexec
upgrade](tpaexec-upgrade.md) to make the required changes to the
cluster.

## Changing a cluster from 2q to EDB repositories

The `--replace-2q-repositories` argument removes any 2ndQuadrant
repositories the cluster uses and adds EDB repositories as required to
replace them.

After reconfiguring with this argument, run [tpaexec
deploy)(tpaexec-deploy.md) to make the required changes to the cluster.

## Output format

The following options control the form of the output:

- `--describe`<br>
  Shows a description of what would be changed, without changing
  anything.

- `--check`<br>
  Validates the changes that would be made and shows any errors any
  errors or warnings that result from validation, without changing
  anything.

- `--output <filename>`<br>
  Writes the output to a file other than config.yml.

## Sample invocation

```
$ tpaexec reconfigure ~/clusters/speedy\
  --architecture PGD-Always-ON\
  --pgd-proxy-routing local
```
