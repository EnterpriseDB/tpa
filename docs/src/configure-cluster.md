# Cluster configuration

With TPAexec, the way to make any configuration change to a cluster is
to edit config.yml and run the provision/deploy/test cycle. The process
is carefully designed to be idempotent, and to make changes only in
response to a change in the configuration or a change on the instances.

The [`tpaexec configure`](tpaexec-configure.md) command will generate
a sensible config.yml file for you, but it covers only the most common
topology and configuration options. If you need something beyond the
defaults, or you need to make changes after provisioning the cluster,
you will need to edit config.yml anyway.

This page is an overview of the configuration mechanisms available.
There's a separate page with more details about the specific
[variables you can set to customise the deployment process](configure-instance.md).

## config.yml

Your `config.yml` file is a
[YAML format](https://yaml.org) text file that represents all aspects of
your desired cluster configuration. Here's a minimal example of a
cluster with two instances:

```yaml
cluster_name: speedy

cluster_vars:
  postgres_version: 9.6

instances:
- node: 1
  Name: one
  role: primary
  platform: docker
  vars:
    ansible_user: root
    x: 42

- node: 2
  Name: two
  role: replica
  platform: docker
  upstream: one
  vars:
    ansible_user: root
    x: 53
```

These three definitions are central to your cluster configuration. The
file may contain many other definitions (including platform-specific
details), but the list of `instances` with `vars` set either for one
instance or for the whole cluster are the basic building blocks of
every TPAexec configuration.

All
[`tpaexec configure`](tpaexec-configure.md)
options translate to config.yml variables in
some way. A single option may affect several variables (e.g.,
`--bdr-version` could set `postgres_version`,
`tpa_2q_repositories`, `extra_postgres_extensions`, and so on), but
you can always accomplish with an editor what you could by running the
command.

In terms of YAML syntax, config.yml as a whole represents a hash with
keys such as `cluster_vars` and `instances`. **You must ensure that
each key is defined only once.** If you were to inadvertently repeat the
`cluster_vars`, say, the second definition would completely override
the former, and your next deployment could make unintended changes
because of missing (shadowed) variables.

TPAexec checks the consistency of the overall cluster topology (for
example, if you declare an instance with the role "replica", you must
also declare the name of its upstream instance, and that instance must
exist), but it will not prevent you from setting any variable you like
on the instances. You must exercise due caution, and try out changes in
a test environment before rolling them out into production.

## Variables

In Ansible terminology, most configuration settings are “inventory
variables”—TPAexec will translate `cluster_vars` into `group_vars`
(that apply to the cluster as a whole) and each instance's `vars` into
`host_vars` in the inventory during provisioning, and deployment will
use the inventory values. After you change config.yml, **you must
remember to run** `tpaexec provision` **before** `tpaexec deploy`.

Any variable can be set for the entire cluster, or an individual host,
or both; host variables override group variables. In practice, setting
`x: 42` in `cluster_vars` is no different from setting it in every
host's `vars`. A host that needs `x` during deployment will see the
value 42 either way. A host will always see the most specific value, so
it is convenient to set some default value for the group and override it
for specific instances as required.

Whenever possible, defining variables in `cluster_vars` and overriding
them for specific instances results in a concise configuration that is
easier to review and change (less repetition). Beyond that, it's up to
you to decide whether any given setting makes more sense as a group or
host variable.

## Cluster variables

The keys under `cluster_vars` may map to any valid YAML type, and will
be translated directly into group variables in the Ansible inventory:

```yaml
cluster_vars:
  postgres_version: 11
  tpa_2q_repositories:
  - products/bdr3/release
  - products/pglogical3/release
  postgres_conf_settings:
    bdr.trace_replay: true
```

In this case, `tpaexec provision` will write three variables (a
string, a list, and a hash) to the inventory in
`group_vars/tag_Cluster_name/01-cluster_name.yml`.

## Instance variables

This documentation uses the term “instance variables” to refer to any
variables that are defined for a specific instance in config.yml. For
example, here's a typical instance definition:

```yaml
instances:
- Name: unwind
  node: 1
  backup: unkempt
  location: a
  role:
  - primary
  - bdr
  volumes:
  - device_name: root
    encrypted: true
    volume_size: 16
    volume_type: gp2
  - device_name: /dev/xvdf
    encrypted: true
    vars:
      volume_for: postgres_data
    volume_size: 64
    volume_type: gp2
  platform: aws
  type: t3.micro
  vars:
    ansible_user: ec2-user
    postgres_conf_directory: /opt/postgres/conf
```

The variables defined in this instance's `vars` will all become host
variables in the inventory, but all host vars in the inventory do not
come from `vars` alone. Some other instance settings, including
`platform`, `location`, `volumes`, and `role` are also copied to the
inventory as host vars (but you cannot define these settings under
`vars` or `cluster_vars` instead).

The settings outside `vars` may describe the properties of the instance
(e.g., `Name` and `node`) or its place in the topology of the cluster
(e.g., `role`, `backup`) or they may be platform-specific attributes
(e.g., instance `type` and `volumes`). Other than knowing that they
cannot be defined under `vars`, it is rarely necessary to distinguish
between these instance “settings” and instance “variables”.

In this case, `tpaexec provision` will write a number of host
variables to the inventory in `host_vars/unwind/01-instance_vars.yml`.

## instance_defaults

This is a mechanism to further reduce repetition in
config.yml. It is most useful for instance settings that cannot be
defined as `cluster_vars`. For example, you could write the following:

```yaml
instance_defaults:
  platform: aws
  type: t3.micro
  tags:
    AWS_ENVIRONMENT_SPECIFIC_TAG_KEY: some_mandated_value

instances:
- node: 1
  Name: one
- node: 2
  Name: two
- …
```

Whatever you specify under `instance_defaults` serves as the default for
every entry in `instances`. In this example, it saves spelling out the
`platform` and `type` of each instance, and makes it easier to change
all your instances to a different type. If any instance specifies a
different value, it will of course take precedence over the default.

It may help to think of `instance_defaults` as being a macro facility to
use in defining `instances`. What is ultimately written to the inventory
comes from the (expanded) definition of `instances` alone. If you're
trying to decide whether to put something in `cluster_vars` or
`instance_defaults`, it probably belongs in the former unless it
_cannot_ be defined as a variable (e.g., `platform` or `type`), which is
true for many platform-specific properties (such as AWS resource tags)
that are used only in provisioning, and not during deployment.

The `instance_defaults` mechanism does nothing to stop you from using it
to fill in the `vars` for an instance (default hash values are merged
with any hash specified in the `instances` entry). However, there is no
particular advantage to doing this rather than setting the same default
in `cluster_vars` and overriding it for an instance if necessary. When
in doubt, use `cluster_vars`.

## Locations

You can also specify a list of `locations` in config.yml:

```yaml
locations:
- Name: first
  az: eu-west-1a
  region: eu-west-1
  subnet: 10.33.110.128/28

- Name: second
  az: us-east-1b
  region: us-east-1
  subnet: 10.33.75.0/24

instances:
- node: 1
  Name: one
  location: first
…
```

If an instance specifies `location: first` (or `location: 0`), the
settings under that location serve as defaults for that instance. Again,
just like `instance_defaults`, an instance may override the defaults
that it inherits from its location. And again, you can use this feature
to fill in `vars` for an instance. This can be useful if you have some
defaults that apply to only half your instances, and different values
for the other half (as with the platform-specific settings in the
example above).

Locations represent a collection of settings that instances can “opt in”
to. You can use them to stand for different data centres, AWS regions,
Docker hosts, or something else entirely. TPAexec does not expect or
enforce any particular interpretation.
