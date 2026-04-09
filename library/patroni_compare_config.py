#!/usr/bin/python
# -*- coding: utf-8 -*-

#  © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.
#
from __future__ import absolute_import, division, print_function

from typing import Any, Dict, Set

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r"""
---
module: patroni_compare_config
short_description: Compares two Patroni configuration dictionaries.
description:
  - Compares an old Patroni configuration dictionary with a new one.
  - Returns added, removed, and modified keys, and the required action (none, reload,
    restart) based on the differences.
options:
  old_config:
    description:
      - The old Patroni configuration as a dictionary.
    type: dict
    required: true
  new_config:
    description:
      - The new Patroni configuration as a dictionary.
    type: dict
    required: true
notes:
  - If the old_config dictionary is empty, all keys from new_config are reported as
    added and the action is "none", as this typically represents a first-time setup.
author: "Israel Barth Rubio <israel.barth@enterprisedb.com>"
"""

EXAMPLES = r"""
- name: Compare Patroni configs
  patroni_compare_config:
    old_config:
      etcd:
        host: 127.0.0.1
        port: 2379
      restapi:
        listen: 0.0.0.0:8009
    new_config:
      etcd3:
        host: 127.0.0.1
        port: 2379
      restapi:
        listen: 0.0.0.0:8008
  register: result

- debug:
    var: result
"""

RETURN = r"""
added:
  description: Keys that were added, with their new values.
  type: dict
  sample: sample: {"etcd3.host": "127.0.0.1", "etcd3.port": 2379}
removed:
  description: Keys that were removed, with their old values.
  type: dict
  sample: {"restapi.connect_address": "192.168.1.100:8008"}
modified:
  description: Keys that were modified, with their old and new values.
  type: dict
  sample: {"restapi.listen": {"old": "127.0.0.1:8008", "new": "0.0.0.0:8008"}}
action:
  description: Required action to apply changes.
  type: str
  sample: "reload"
changed:
  description: Whether the module detected any changes.
  type: bool
  sample: true
"""

# Configuration options which require a restart of the Patroni agent upon changes
RESTART_KEYS: Set[str] = {
    "etcd3.cacert",
    "etcd3.cert",
    "etcd3.key",
    "etcd3.username",
    "etcd3.password",
}


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, str]:
    """
    Flatten a nested dictionary into dot-separated keys.

    :param d: The dictionary to flatten.
    :param parent_key: The base key string (used for recursion).
    :param sep: The separator to use between keys.

    :return: A flattened dictionary with dot-separated keys.
    """
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def compare_dicts(
    old_flat: Dict[str, Any], new_flat: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Compare two flattened dictionaries and return the differences.

    :param old_flat: The old flattened dictionary.
    :param new_flat: The new flattened dictionary.

    :return: A dictionary containing the differences. The keys are ``added``,
        ``removed``, and ``modified``.
    """
    added = {k: new_flat[k] for k in new_flat if k not in old_flat}
    removed = {k: old_flat[k] for k in old_flat if k not in new_flat}
    modified = {
        k: {"old": old_flat[k], "new": new_flat[k]}
        for k in old_flat
        if k in new_flat and old_flat[k] != new_flat[k]
    }
    return {"added": added, "removed": removed, "modified": modified}


def run_module() -> None:
    """
    Run the Ansible module.
    """
    module = AnsibleModule(
        argument_spec={
            "old_config": {"type": "dict", "required": True},
            "new_config": {"type": "dict", "required": True},
        },
        supports_check_mode=True,
    )

    old_config: Dict[str, Any] = module.params["old_config"]  # type: ignore
    new_config: Dict[str, Any] = module.params["new_config"]  # type: ignore

    # Handle the case where the old configuration is empty (first run).
    if not old_config:
        # If the new config has keys, they are all considered 'added'.
        # The action is 'none' because this is a first-time setup, not a modification.
        module.exit_json(
            changed=True,
            action="none",
            added=flatten_dict(new_config),
            removed={},
            modified={},
        )

    old_flat = flatten_dict(old_config)
    new_flat = flatten_dict(new_config)

    differences = compare_dicts(old_flat, new_flat)
    action = "none"

    if any(differences.values()):
        all_changed_keys = (
            set(differences["added"])
            | set(differences["removed"])
            | set(differences["modified"])
        )

        action = "restart" if all_changed_keys & RESTART_KEYS else "reload"

    module.exit_json(changed=(action != "none"), action=action, **differences)


def main() -> None:
    """
    Main entry point for the module.
    """
    run_module()


if __name__ == "__main__":
    main()
