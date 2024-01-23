# Cluster configuration

With TPA, the way to make any configuration change to a cluster is
to edit `config.yml` and run the provision/deploy/test cycle. The process
is carefully designed to be idempotent and to make changes only in
response to a change in the configuration or on the instances.

The [`tpaexec configure`](tpaexec-configure.md) command generates
a sensible `config.yml` file for you, but it covers only the most common
topology and configuration options. If you need something beyond the
defaults, or you need to make changes after provisioning the cluster,
you need to edit `config.yml`.

An overview of the configuration mechanisms available follows.
For more details about the specific
variables you can set to customize the deployment process, 
see [Instance configuration](configure-instance.md).

## config.yml

Your `config.yml` file is a
[YAML format](https://yaml.org) text file that represents all aspects of
your desired cluster configuration. Here's a minimal example of a
cluster with two instances:

```yaml
cluster_name: speedy

cluster_vars:
  postgres_version: 14

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
file might contain many other definitions (including platform-specific
details), but the list of `instances` with `vars` set either for one
instance or for the whole cluster are the basic building blocks of
every TPA configuration.

All
[`tpaexec configure`](tpaexec-configure.md)
options translate to `config.yml` variables in
some way. A single option can affect several variables. (For example,
`--bdr-version` might set `postgres_version`,
`tpa_2q_repositories`, `edb_repositories`, `extra_postgres_extensions`, and so on.) But
you can always accomplish with an editor the same things you can by running the
command.

In terms of YAML syntax, `config.yml` as a whole represents a hash with
keys such as `cluster_vars` and `instances`. 

!!! Note
    You must ensure that
    each key is defined only once. If you were to inadvertently repeat the
    `cluster_vars`, say, the second definition would completely override
    the first, and your next deployment could make unintended changes
    because of missing (shadowed) variables.

TPA checks the consistency of the overall cluster topology. For
example, if you declare an instance with the replica role, you must
also declare the name of its upstream instance, and that instance must
exist. However, TPA doesn't prevent you from setting variables
on the instances. Exercise due caution and try out changes in
a test environment before rolling them out into production.

## Variables

In Ansible terminology, most configuration settings are “inventory
variables.” TPA translates `cluster_vars` into `group_vars`
that apply to the cluster as a whole and each instance's `vars` into
`host_vars` in the inventory during provisioning. Deployment then
uses the inventory values. 

!!! Note
    After you change `config.yml`, 
    remember to run `tpaexec provision` before `tpaexec deploy`.

You can set any variable for the entire cluster, an individual host,
or both. Host variables override group variables. In practice, setting
`x: 42` in `cluster_vars` is the same as setting it in every
host's `vars`. A host that needs `x` during deployment sees the
value 42 either way. A host always sees the most specific value, so
it's convenient to set some default value for the group and override it
for specific instances as required.

Whenever possible, defining variables in `cluster_vars` and overriding
them for specific instances results in a concise configuration. because 
there's less repetition, it's easier to review and change. Beyond that, it's up to
you to decide whether any given setting makes more sense as a group or
host variable.

## Cluster variables

The keys under `cluster_vars` can map to any valid YAML type and are
translated directly into group variables in the Ansible inventory:

```yaml
cluster_vars:
  postgres_version: 14
  tpa_2q_repositories:
  - products/bdr3/release
  - products/pglogical3/release
  postgres_conf_settings:
    bdr.trace_replay: true
```

In this case, `tpaexec provision` writes three variables (a
string, a list, and a hash) to the inventory in
`group_vars/tag_Cluster_name/01-cluster_name.yml`.

## Instance variables

We use the term “instance variables” to refer to any
variables that are defined for a specific instance in `config.yml`. This
example shows a typical instance definition:

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
variables in the inventory, but all host vars in the inventory don't
come from `vars` alone. Some other instance settings, including
`platform`, `location`, `volumes`, and `role`, are also copied to the
inventory as host `vars`. However, you can't define these settings under
`vars` or `cluster_vars` instead.

The settings outside `vars` can describe the properties of the instance
(such as `Name` and `node`) or its place in the topology of the cluster
(such as `role` and `backup`). Or they can be platform-specific attributes
(such as instance `type` and `volumes`). Other than knowing that they
can't be defined under `vars`, it's rarely necessary to distinguish
between these instance settings and instance variables.

In this case, `tpaexec provision` writes a number of host
variables to the inventory in `host_vars/unwind/01-instance_vars.yml`.
<!-- In which case? -->
## instance_defaults

This setting is a mechanism to further reduce repetition in
`config.yml`. It's most useful for instance settings that can't be
defined as `cluster_vars`. For example, you can write the following:

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
`platform` and `type` of each instance and makes it easier to change
all your instances to a different type. If any instance specifies a
different value, that value takes precedence over the default.

It might help to think of `instance_defaults` as being a macro facility to
use in defining `instances`. What's ultimately written to the inventory
comes from the (expanded) definition of `instances` alone. If you're
trying to decide whether to put something in `cluster_vars` or
`instance_defaults`, it probably belongs in the former unless it
can't be defined as a variable (for example, `platform` or `type`). This is
true for many platform-specific properties, such as AWS resource tags,
that are used only in provisioning and not during deployment.

The `instance_defaults` mechanism does nothing to stop you from using it
to fill in the `vars` for an instance. (Default hash values are merged
with any hash specified in the `instances` entry.) However, there isn't a
particular advantage to doing this rather than setting the same default
in `cluster_vars` and overriding it for an instance if necessary. When
in doubt, use `cluster_vars`.

## Locations

You can also specify a list of `locations` in `config.yml`:

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
settings under that location serve as defaults for that instance. 
Just like `instance_defaults`, an instance can override the defaults
that it inherits from its location. Similarly, you can use this feature
to fill in `vars` for an instance. This approach can be useful if you have some
defaults that apply to only half your instances and different values
for the other half, as with the platform-specific settings in the
example.

Locations represent a collection of settings that instances can “opt in”
to. You can use them to stand for different data centers, AWS regions,
Docker hosts, or something else. TPA doesn't expect or
enforce any particular interpretation.
