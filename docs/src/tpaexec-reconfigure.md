# tpaexec reconfigure

The `tpaexec reconfigure` command reads config.yml and generates a
revised version of it that changes the cluster from one architecture to
another. [tpaexec upgrade](tpaexec-upgrade.md) may then be invoked to
make the required changes on the instances that make up the cluster.

## Arguments

As with other tpaexec commands, the cluster directory must always be
given.

The following arguments control the contents of the new config.yml:

- `--architecture <architecture>`(required)<br>
The new architecture for the cluster. At present the only supported
architecture is `PGD-Always-ON`

- `--pgd-proxy-routing <global|local>`(required)<br>
How PGD-Proxy is to route connections. See
[the PGD-Always-ON documentation](architecture-PGD-Always-ON) for more
information about the meaning of this argument.

- `--edb-repositories <repositories>`(optional)<br>
A space-separated list of EDB package repositories. It is usually
unnecessary to specify this; `tpaexec configure` will choose a suitable
repository based on the postgres flavour in use in the cluster.


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
