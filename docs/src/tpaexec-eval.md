---
description: A command to check facts about the TPA installation.
---


# tpaexec eval

You can use the eval command to evaluate an arbitrary Jinja/Ansible expression in the context of the cluster's inventory.
The information can be related to variables, inventory, gathered OS facts, computed paths, package names, etc.

## Usage

* Run `tpaexec eval ~/clusters/speedy '<expression>'`

### Options

* `tpaexec eval ~/clusters/speedy '<expression>' --hosts <pattern>`

    Restrict evaluation to a host pattern. The pattern can be a single
    instance name (`unreal`), a colon-separated list (`unreal:ultra`),
    `localhost`, or a group name (`role_primary`, `role_etcd`).

* `tpaexec eval ~/clusters/speedy '<expression>' --no-init`

    Skip the cluster initialisation playbook. Only variables derived
    from `config.yml` and the generated inventory are available;
    `ansible_*` host facts will be undefined. Recommended for quick
    inventory inspection.

## Example Output

Look up a value from `config.yml` for a single host:

```shell
tpaexec eval ~/clusters/speedy '{{ postgres_version }}' --no-init --hosts unreal
```
```output
  unreal => {
    "msg": "17"
}
```

Print a value for every host in the cluster:

```shell
tpaexec eval ~/clusters/speedy '{{ ip_address }}' --no-init
```
```output
  unreal => {
    "msg": "10.33.155.2"
}
  ultra => {
    "msg": "10.33.155.3"
}
  quondam => {
    "msg": "10.33.155.4"
}
```

Inspect inventory-wide data by targeting `localhost`:

```shell
tpaexec eval ~/clusters/speedy '{{ groups.keys() | list }}' --no-init --hosts localhost
```
```output
  localhost => {
    "msg": [
        "all",
        "ungrouped",
        "tag_Cluster_speedy"
    ]
}
```

List every variable defined for a host (useful when you don't yet know
the name of the variable you want):

```shell
tpaexec eval ~/clusters/speedy '{{ hostvars[inventory_hostname].keys() | list | sort }}' --no-init --hosts unreal
```
```output
  unreal => {
    "msg": [
        "ansible_user",
        "backup",
        "cluster_name",
        "failover_manager",
        "ip_address",
        "postgres_version",
        "role",
        "..."
    ]
}
```

Read a fact gathered from the host itself (omit `--no-init` so the
initialisation playbook runs and populates `ansible_*` facts):

```shell
tpaexec eval ~/clusters/speedy '{{ ansible_distribution }}' --hosts unreal
```
```output
  unreal => {
    "msg": "Debian"
}
```