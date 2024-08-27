---
description: The command that creates and configures a new cluster.
---


# Cluster configuration

The `tpaexec configure` command generates a YAML cluster configuration
file that is required by subsequent stages in the provision/deploy/test
cycle.

## Quickstart

```bash
[tpa]$ tpaexec configure ~/clusters/speedy --architecture M1 \
        --postgresql 14 \
        --failover-manager repmgr
```

This command will create a directory named `~/clusters/speedy` and
generate a configuration file named `config.yml` that follows the
layout of the architecture named M1 (single primary, N replicas).
It will create a git repository in the new directory and make an initial
commit containing the generated `config.yml`.

The command also accepts various options (some specific to the selected
architecture or platform) to modify the configuration, but the defaults
are sensible and intended to be usable straightaway. You are encouraged
to read the generated config.yml and fine-tune the configuration to suit
your needs. (Here's an overview of [configuration settings that affect
the deployment](configure-instance.md).)

It's possible to write config.yml entirely by hand, but it's much easier
to edit the generated file.

## Configuration options

The first argument must be the cluster directory, e.g., `speedy` or
`~/clusters/speedy` (the cluster will be named speedy in both cases).
We recommend that you keep all your clusters in a common directory,
e.g., `~/clusters` in the example above.

The next argument must be `--architecture <name>` to select an
architecture, e.g.,
[M1](architecture-M1.md) or
[BDR-Always-ON](architecture-BDR-Always-ON.md).
For a complete list of architectures, run
`tpaexec info architectures`.

Next, you must specify a [flavour and version of
Postgres](#postgres-flavour-and-version) to install.

The arguments above are always mandatory. The rest of the options
described here may be safely omitted, as in the example above; the
defaults will lead to a usable result.

Run `tpaexec help configure-options` for a list of common options.

### Architecture-specific options

The architecture you select determines what other options are accepted.
Typically, each architecture accepts some unique options as well as the
generic options described below.

For example, with M1 you can use `--location-names l1 l2` to create
a cluster with nodes in two named locations. Please consult the
documentation for an architecture for a list of options that it accepts
(or, in some cases, requires).

### Platform options

Next, you may use `--platform <name>` to select a platform, e.g.,
[aws](platform-aws.md) or [bare](platform-bare.md).

An architecture may or may not support a particular platform. If not, it
will fail to configure the cluster.

The choice of platform affects the interpretation of certain options.
For example, if you choose aws, the arguments to
`--region <region>` and
`--instance-type <type>`
must be a valid
[AWS region name](https://docs.aws.amazon.com/general/latest/gr/rande.html)
and
[EC2 instance type](https://aws.amazon.com/ec2/instance-types/)
respectively. Please refer to the platform documentation for more details.

If you do not explicitly select a platform, the default is currently
aws.

**Note:** TPA fully supports creating clusters with instances on
different platforms, but `tpaexec configure` cannot currently generate
such a configuration. You must edit config.yml to specify multiple
platforms.

### Owner

Specify `--owner <name>` to associate the cluster (by some
platform-specific means, e.g., AWS tags) with the name of a person
responsible for it. This is especially important for cloud platforms. By
default, the owner is set to the login name of the user running
`tpaexec provision`.

(You may use your initials, or "Firstname Lastname", or anything else
that identifies you uniquely.)

### Region

Specify `--region <region>` to select a region.

This option is meaningful only for cloud platforms. The default for AWS
is eu-west-1.

**Note:** TPA fully supports creating clusters that span multiple
regions, but `tpaexec configure` cannot currently generate such a
configuration. You must edit config.yml to specify multiple regions.

### Network configuration

By default, each cluster will be configured with a number of randomly selected
`/28` subnets from the CIDR range `10.33.0.0/16`, depending on the selected
architecture.

Specify `--network 192.168.0.0/16` to assign subnets from a different network.

**Note:** On AWS clusters, this corresponds to the VPC CIDR.
See [aws](platform-aws.md#vpc-required) documentation for details.

Specify `--subnet-prefix 26` to assign subnets of a different size, /26 instead
of /28 in this case.

Specify `--no-shuffle-subnets` to allocate subnets from the start of the
network CIDR range, without randomisation, e.g. `10.33.0.0/28`, then
`10.33.0.16/28` and so on.

Specify `--exclude-subnets-from <directory>` to exclude subnets that are
already used in existing cluster config.yml files. You can specify this
argument multiple times for each directory.

**Note:** These options are not meaningful for the "bare" platform, where
TPA will not alter the network configuration of existing servers.

### Instance type

Specify `--instance-type <type>` to select an instance type.

This option is meaningful only for cloud platforms. The default for AWS
is t3.micro.

### Disk space

Specify `--root-volume-size 64` to set the size of the root volume in
GB. (Depending on the platform, there may be a minimum size required for
the root volume.)

The `--postgres-volume-size <size>` and
`--barman-volume-size <size>` options are available to set the sizes
of the Postgres and Barman volumes on those architectures and platforms
that support separate volumes for Postgres and Barman.

None of these options is meaningful for the "bare" platform, where
TPA has no control over volume sizes.

### Hostnames

By default, `tpaexec configure` will randomly select as many hostnames
as it needs from a pre-approved list of several dozen names. This should
be enough for most clusters.

Specify `--hostnames-from <filename>` to select hostnames from a file
with one name per line. The file must contain at least as many valid
hostnames as there are instances in your cluster. Each line may contain
an optional IP address after the name; if present, this address will be
set as the `ip_address` for the corresponding instance in `config.yml`.

Use `--hostnames-pattern '…pattern…'` to limit the selection to
lines matching an egrep pattern.

Use `--hostnames-sorted-by="--dictionary-order"` to select a sort(1)
option other than `--random-sort` (which is the default).

Use `--hostnames-unsorted` to not sort hostnames at all. In this case,
they will be assigned in the order they are found in the hostnames file.
This is the default when a hostnames file is explicitly specified.

Use `--cluster-prefixed-hostnames` to make each hostname begin with the
name of the cluster. This can be useful to avoid hostname clashes when
running more than one docker cluster on the same host.

Hostnames may contain only letters (a-z), digits (0-9), and '-'. They
may be FQDNs, depending on the selected platform. Hostnames should be
in lowercase; any uppercase characters will be converted to lowercase
internally, and any references to these hostnames in config.yml (e.g.,
`upstream: hostname`) must use the lowercase version.

## Software selection

### Distribution

Specify `--distribution <name>` to select a distribution.

The selected platform determines which distributions are available, and
which one is used by default.

In general, you should be able to use "Debian", "RedHat", "Ubuntu", and
"SLES" to select the right images.

This option is not meaningful for the "bare" platform, where TPA has
no control over which distribution is installed.

### EDB repositories

TPA can enable any EDB software repository that you have
access to through a subscription. By default, TPA will install any
product repositories that the architecture requires.

More detailed explanation of how TPA uses EDB
repositories is available [here](edb_repositories.md) and on the page
for each architecture.

Specify ``--edb-repositories repository …`` to specify the complete list
of EDB repositories to install on each instance.

Use this option with care. TPA will configure the named repositories
with no attempt to make sure the combination is appropriate.

To use this options, you must ``export EDB_SUBSCRIPTION_TOKEN=xxx``
before you run TPA.
You can get an EDB token from enterprisedb.com/repos.

### Local repository support

Use `--enable-local-repo` to create a local package repository from
which to ship packages to target instances.

In environments with restricted network access, you can instead use
`--use-local-repo-only` to create a local repository and disable all
other package repositories on target instances, so that packages are
installed only from the local repository.

The page about [Local repository support](local-repo.md) has more
details.

### Software versions

#### Postgres flavour and version

TPA supports PostgreSQL, EDB Postgres Extended, and EDB Postgres
Advanced Server (EPAS) versions 11 through 16.

You must specify both the flavour (or distribution) and major version of
Postgres to install, for example:

* `--postgresql 14` will install PostgreSQL 14

* `--edb-postgres-extended 15` will install EDB Postgres Extended 15

* `--edb-postgres-advanced 15 --redwood` will install EPAS 15 in
  "Redwood" mode

* `--edb-postgres-advanced 15 --no-redwood` will install EPAS 15 in
  non-Redwood mode

If you are installing EPAS, you must specify whether it should operate
in `--redwood` or `--no-redwood` mode, i.e., whether to enable or
disable its Oracle compatibility features.

Installing EDB Postgres Extended or Postgres Advanced Server requires
a valid [EDB repository subscription](edb_repositories.md).

#### Package versions

By default, we always install the latest version of every package. This
is usually the desired behaviour, but in some testing scenarios, it may
be necessary to select specific package versions using any of the
following options:

1. `--postgres-package-version 10.4-2.pgdg90+1`
2. `--repmgr-package-version 4.0.5-1.pgdg90+1`
3. `--barman-package-version 2.4-1.pgdg90+1`
4. `--pglogical-package-version '2.2.0*'`
5. `--bdr-package-version '3.0.2*'`
6. `--pgbouncer-package-version '1.8*'`

You may use any version specifier that apt or yum would accept.

If your version does not match, try appending a `*` wildcard. This
is often necessary when the package version has an epoch qualifier
like `2:...`.

You may also specify `--extra-packages p1 p2 …` or
`--extra-postgres-packages p1 p2 …` to install additional packages.
The former lists packages to install along with system packages, while
the latter lists packages to install later along with postgres packages.
(If you mention packages that depend on Postgres in the former list, the
installation will fail because Postgres will not yet be installed.) The
arguments are passed on to the package manager for installation without
any modifications.

The `--extra-optional-packages p1 p2 …` option behaves like
`--extra-packages`, but it is not an error if the named packages
cannot be installed.

### Known issue with wildcard use

Please note that the use of wildcards in `*_package_version` when added
permanently to `config.yml`, can result in unexpected updates to
installed software during `tpaexec deploy` on nodes with RHEL 8 and
above (or derivative OSs which use dnf such as Rocky Linux).
When deploy runs on an existing cluster that already has packages
installed ansible may be unable to match the full package version.
For example, if the value for `bdr_package_version` was set to `3.6*`
then ansible would not be able to match this to an installed version of
PGD, it would assume no package is installed, and it would attempt to
install the latest version available of the package with the same name
in the configured repository, e.g. 3.7.

We are aware of this limitation as an ansible dnf module bug and hope
to address this in a future release of TPA.

### Building and installing from source

If you specify `--install-from-source postgres`, Postgres will be
built and installed from a git repository instead of installed from
packages. By default, this will build the appropriate
`REL_nnn_STABLE` branch.

You may use `--install-from-source postgres bdr5` to
build and install both components from source, or just use
`--install-from-source bdr5` to use packages for
Postgres, but build and install PGD v5 from source.
By default, this will build the `main` branch of PGD.

To build a different branch, append `:branchname` to the corresponding
argument. For example `--install-from-source 2ndqpostgres:dev/xxx`, or
`pglogical:bug/nnnn`.

You may not be able to install packages that depend on a package that
you chose to replace with a source installation instead. For example,
PGD v3 packages depend on pglogical v3 packages, so you can't install
pglogical from its source repository and PGD from packages. Likewise,
you can't install Postgres from source and pglogical from packages.

## Overrides

You may optionally specify `--overrides-from a.yml …` to load one or
more YAML files with settings to merge into the generated config.yml.

Any file specified here is first expanded as a Jinja2 template, and the
result is loaded as a YAML data structure, and merged recursively into
the arguments used to generate config.yml (comprising architecture and
platform defaults and arguments from the command-line). This process is
repeated for each additional override file specified; this means that
settings defined by one file will be visible to any subsequent files.

For example, your override file might contain:

```
cluster_tags:
  some_tag: "{{ lookup('env', 'SOME_ENV_VAR') }}"

cluster_vars:
  synchronous_commit: remote_write
  postgres_conf_settings:
    effective_cache_size: 4GB
```

These settings will augment `cluster_tags` and `cluster_vars` that
would otherwise be in config.yml. Settings are merged recursively, so
`cluster_tags` will end up containing both the default Owner tag as
well as `some_tag`. Similarly, the `effective_cache_size` setting
will override that variable, leaving other `postgres_conf_settings`
(if any) unaffected. In other words, you can set or override specific
subkeys in config.yml, but you can't empty or replace `cluster_tags`
or any other hash altogether.

The merging only applies to hash structures, so you cannot use this
mechanism to change the list of `instances` within config.yml. It is
most useful to augment `cluster_vars` and `instance_defaults` with
common settings for your environment.

That said, the mechanism does not enforce any restrictions, so please
exercise due caution. It is a good idea to generate two configurations
with and without the overrides and diff the two config.yml files to make
sure you understand the effect of all the overrides.

## Ansible Tower

Use the `--use-ansible-tower` and `--tower-git-repository` options to
create a cluster adapted for deployment with Ansible Tower. See [Ansible
Tower](tower.md) for details.

## Beacon agent

Use the `--enable-beacon-agent` and `--beacon-agent-project-id` options
to install the beacon agent, which enables you to view your cluster in
the EDB Postgres AI Console. See [Configuring the beacon
agent](beacon-agent.md) for details.

## Git repository

By default, a git repository is created with an initial branch named
after the cluster, and a single commit is made, with the configure
options you used in the commit message. If you don't have git in your
`$PATH`, tpaexec will not raise an error but the repository will not be
created. To suppress creation of the git repository, use the `--no-git`
option. (Note that in an Ansible Tower cluster, a git repository is
required and will be created later by `tpaexec provision` if it does not
already exist.)

## Keyring backend for vault password

TPA generates a cluster specific ansible vault password.
This password is used to encrypt other sensitive variables generated
for the cluster, postgres user password, barman user password and so on.

Keyring backend `system` will leverage the best keyring backend on your system
from the list of supported backend by python keyring module including
gnome-keyring and secret-tool.

Default is to store the vault password using `system` keyring for new cluster.
removing `keyring_backend: system` in config.yml file **before** any `provision`
will revert previous default to store vault password in plaintext file.

Using `keyring_backend: system` also generates a `vault_name` entry in config.yml
used to store the vault password unique storage name. TPA generate an UUID by
default but there is no naming scheme requirements.

Note: When using `keyring_backend: system` and the same base config.yml file
for multiple clusters with same `cluster_name`, by copying the config file to
a different location, ensure the value pair (`vault_name`, `cluster_name`)
is unique for each cluster copy.

Note: When using `keyring_backend: system` and moving an already provisioned
cluster folder to a different tpa host, ensure that you export the associated
vault password on the new machine's system keyring. vault password can be
displayed via `tpaexec show-vault <cluster_dir>`.

## Examples

Let's see what happens when we run the following command:

```bash
[tpa]$ tpaexec configure ~/clusters/speedy --architecture M1 \
        --distribution Debian \
        --platform aws --region us-east-1 --network 10.33.0.0/16 \
        --instance-type t2.medium --root-volume-size 32 \
        --postgres-volume-size 64 --barman-volume-size 128 \
        --postgresql 14 \
        --failover-manager repmgr
[tpa]$
```

There is no output, so there were no errors. The cluster directory has
been created and populated.

```bash
$ ls -lh ~/clusters/speedy/
total 8.0K
drwxrwxr-x 2 haroon haroon 4.0K Aug 17 02:33 commands
-rw-rw-r-- 1 haroon haroon 1.5K Aug 17 02:33 config.yml
lrwxrwxrwx 1 haroon haroon   53 Aug 17 02:33 deploy.yml -> /home/haroon/tpa/architectures/M1/deploy.yml
```

The cluster configuration is in config.yml, and its neighbours are links
to architecture-specific support files that you need not interact with
directly. Here's what the configuration looks like:

```yaml
---
architecture: M1
cluster_name: speedy
cluster_tags: {}

keyring_backend: system
vault_name: cfae3da3-ec00-46cd-ab05-e153f1c788db

cluster_rules:
- cidr_ip: 0.0.0.0/0
  from_port: 22
  proto: tcp
  to_port: 22
- cidr_ip: 10.33.120.80/28
  from_port: 0
  proto: tcp
  to_port: 65535
ec2_ami:
  Name: debian-11-amd64-20240104-1616
  Owner: '136693071363'
ec2_instance_reachability: public
ec2_vpc:
  us-east-1:
    Name: Test
    cidr: 10.33.0.0/16

cluster_vars:
  edb_repositories: []
  failover_manager: repmgr
  postgres_flavour: postgresql
  postgres_version: '14'
  preferred_python_version: python3
  use_volatile_subscriptions: false

locations:
- Name: main
  az: us-east-1a
  region: us-east-1
  subnet: 10.33.120.80/28

instance_defaults:
  default_volumes:
  - device_name: root
    encrypted: true
    volume_size: 32
    volume_type: gp2
  - device_name: /dev/sdf
    encrypted: true
    vars:
      volume_for: postgres_data
    volume_size: 64
    volume_type: gp2
  platform: aws
  type: t2.medium
  vars:
    ansible_user: admin

instances:
- Name: uproar
  backup: kinsman
  location: main
  node: 1
  role:
  - primary
- Name: unravel
  location: main
  node: 2
  role:
  - replica
  upstream: uproar
- Name: kinsman
  location: main
  node: 3
  role:
  - barman
  - log-server
  - witness
  upstream: uproar
  volumes:
  - device_name: /dev/sdf
    encrypted: true
    vars:
      volume_for: barman_data
    volume_size: 128
    volume_type: gp2
```

The next step is to run [`tpaexec provision`](tpaexec-provision.md)
or learn more about how to customise the configuration of
[the cluster as a whole](configure-cluster.md) or how to configure an
[individual instance](configure-instance.md).
