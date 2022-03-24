#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.
"""
Instance filters.

The filters defined here take the array of instances (from config.yml)
and other inputs and return a new array of instances with parameters
suitably adjusted.

"""

import copy
import re
from ansible.errors import AnsibleFilterError

VOLUME_TRANSLATIONS = {
    "barman_data": {"mountpoint": "/var/lib/barman"},
    "postgres_data": {"mountpoint": "/opt/postgres"},
    "postgres_wal": {"mountpoint": "/opt/postgres/wal"},
    "postgres_tablespace": {
        "mountpoint": "/opt/postgres/tablespaces/{v[tablespace_name]}"
    },
}


def ip_addresses(instance):
    """
    Returns a hash of the IP addresses specified for a given instance.

    Args:
        instance: Instance dict

    """
    addresses = {}
    for a in ["ip_address", "public_ip", "private_ip"]:
        ip = instance.get(a)
        if ip is not None:
            addresses[a] = ip

    return addresses


def deploy_ip_address(instance):
    """
    Returns the IP address that TPAexec should use to ssh to an instance.

    The public_ip, ip_address, and private_ip are used in order of decreasing preference.

    Args:
        instance: Instance dict

    """
    return (
        instance.get("public_ip")
        or instance.get("ip_address")
        or instance.get("private_ip")
    )


def set_instance_defaults(old_instances, cluster_name, instance_defaults, locations):
    """
    Every instance must have certain settings (e.g., tags) in a specific format.

    Args:
        old_instances: List of instances containing dictionaries with instance information.
        cluster_name: Name of the cluster.
        instance_defaults: Dictionary containing defaults
        locations: List of cluster locations

    """
    instances = []

    locations_map = {}
    for location in locations:
        locations_map[location["Name"]] = location

    for old_instance in old_instances:
        new_instance = copy.deepcopy(old_instance)
        tags = new_instance.get("tags", {})

        update_instance_name(new_instance, cluster_name, tags)

        # Anything set in instance_defaults should be copied to the instance,
        # unless the instance has a setting that overrides the default. As a
        # convenience, we also merge dict keys (so that once can, for example,
        # set some vars in instance_defaults and some on the instance, and get
        # all of them, with the instance settings overriding the defaults).

        new_instance.update(
            merged_defaults(
                new_instance, instance_defaults, omit_keys=["default_volumes"]
            )
        )

        update_instance_volume_defaults(new_instance, instance_defaults)

        update_instance_location(new_instance, locations, locations_map)

        # The upstream, backup, and role tags should be moved one level up if
        # they're specified at all.

        for t in ["upstream", "backup", "role"]:
            if t in tags:
                new_instance[t] = tags[t]
                del tags[t]

        # The role tag should be a list, so we convert comma-separated
        # strings if that's what we're given.

        role = new_instance.get("role", [])
        if not isinstance(role, list):
            role = [x.strip() for x in role.split(",")]

        # primary/replica instances must also be tagged 'postgres'.

        if "primary" in role or "replica" in role:
            if "postgres" not in role:
                role = role + ["postgres"]

        new_instance["role"] = role
        new_instance["tags"] = tags

        # Name and node should be in tags, but we'll add them in when we're
        # actually creating the tags, not before.

        for t in ["name", "Name", "node"]:
            if t in tags:
                del tags[t]

        instances.append(new_instance)

    return instances


def update_instance_location(instance, locations, locations_map=None):
    """
    Update instance dict location attribute.

    If the instance specifies «location: x», where x is either a name or
    an array index (for backwards compatibility), we copy the settings
    from location x to the instance, in exactly the same way as we do
    above for instance_defaults.

    Args:
        instance: Instance dictionary
        locations: Location list of dicts
        locations_map: Location list as a map with Name attr as key name

    """
    locations = locations or []
    locations_map = locations_map or {}
    location = instance.get("location", None)
    if len(locations) > 0 and location is not None:
        if isinstance(location, int) and location < len(locations):
            location_defaults = locations[location]
            instance["location"] = locations[location]["Name"]
        elif location in locations_map:
            location_defaults = locations_map[location]
        else:
            raise AnsibleFilterError(
                f"Instance {instance['Name']} specifies unknown location {location}"
            )

        instance.update(
            merged_defaults(instance, location_defaults, omit_keys=["Name"])
        )


def update_instance_volume_defaults(instance, defaults):
    """
    Update instance dict volumes attribute.

    If instance_defaults specifies 'default_volumes', we merge those
    entries with the instance's 'volumes', with entries in the latter
    taking precedence over default entries with the same device name.
    (Setting 'volumes' to [] explicitly in instances will remove the
    defaults altogether.)

    Args:
        instance: Dict containing instance data
        defaults: Dict containing defaults

    """
    volumes = instance.get("volumes", [])
    default_volumes = defaults.get("default_volumes", [])
    if default_volumes and (len(volumes) > 0 or "volumes" not in instance):
        volume_map = {}
        for vol in default_volumes + volumes:
            name = vol.get("raid_device", vol.get("device_name"))
            if name.startswith("/dev/"):
                name = name[5:]
            volume_map[name] = vol

        volumes = []
        for name in sorted(volume_map.keys()):
            volumes.append(volume_map[name])

        instance["volumes"] = volumes


def update_instance_name(instance, cluster_name, tags):
    """
    Update the instance dictionary name attribute.

    Every instance must have a sensible name (lowercase, without underscores).
    If it's set under .tags, we'll move it up.

    Args:
        cluster_name: Name of the cluster
        instance: Instance dict to operate on
        tags: Tags assigned to cluster

    """
    name = instance.get("Name", tags.get("Name", None))
    if name is None:
        name = cluster_name + "-" + str(instance["node"])
    instance["Name"] = name.replace("_", "-").lower()
    instance["vars"] = instance.get("vars", {})


def merged_defaults(item, defaults, omit_keys=None):
    """
    Returns a mapping with merged the keys form defaults.

    Excluding those given in omit_keys, and the corresponding values from item (if specified) or from
    defaults otherwise. Any dict values are further merged for convenience, so that defaults can specify
    some keys and item can override or extend them.

    Args:
        item: Original dict
        defaults: Defaults dict
        omit_keys: Keys to skip during merging

    """
    omit_keys = omit_keys or []
    result = {}

    for key in [k for k in defaults if k not in omit_keys]:
        result[key] = item.get(key, defaults[key])
        if isinstance(result[key], dict) and isinstance(defaults[key], dict):
            b = copy.deepcopy(defaults[key])
            b.update(result[key])
            result[key] = b

    return result


def expand_instance_volumes(old_instances):
    """
    Perform generic instance volume transformation.

    This includes:
    * Strip volumes with the type "none"

    See aws specific transformations in filter_plugins/aws.py

    """
    instances = []
    for instance in old_instances:
        transform = copy.deepcopy(instance)

        volumes = []
        for vol in transform.get("volumes", []):
            volume = copy.deepcopy(vol)
            _vars = volume.get("vars", {})

            volume_type = volume.get("volume_type")
            if volume_type == "none":
                continue

            validate_volume_for(volume["device_name"], _vars)

            volumes.append(volume)

        transform["volumes"] = volumes
        instances.append(transform)

    return instances


def validate_volume_for(device_name, _vars) -> None:
    """
    Validate volume device name with `volume_for` attribute against volume_translations map.

    Given a device name and a container with settings for that device, raises an
    exception if the volume has an invalid volume_for annotation or is missing
    any other required configuration; returns silently otherwise.

    Called during both provisioning and deployment, when `volumes` means two
    different things; expand_instance_volumes() passes in `volumes[*].vars` from
    config.yml, which is translated into an entry in `volumes` in the inventory,
    which is what translate_volume_deployment_defaults() later passes in. This
    is why the function takes "vars", and not "vol".

    See roles/platforms/common/tasks/volumes.yml for more details.
    """
    volume_for = _vars.get("volume_for")
    if volume_for and volume_for not in VOLUME_TRANSLATIONS:
        raise AnsibleFilterError(
            f"volume {device_name} has unrecognised volume_for={volume_for}"
        )

    if volume_for == "postgres_tablespace" and not _vars.get("tablespace_name"):
        raise AnsibleFilterError(
            f"volume {device_name} is {volume_for}; must define tablespace_name"
        )


def translate_volume_deployment_defaults(vol):
    """
    Update volume dict attr defaults.

    Modifies the given entry from `volumes` in the inventory to translate its
    volume_for into a mountpoint and other volume defaults if needed. Meant to
    be used only as a |map function.

    See roles/platforms/common/tasks/volumes.yml for more details.

    Args:
        vol: Dict containing volume data, including to `volume_for`, `mountpoint` types and `encryption`

    """
    validate_volume_for(vol["device"], vol)

    # If we have a valid volume_for, we can translate that into a default
    # mountpoint (unless one is explicitly set).
    volume_for = vol.get("volume_for")
    if volume_for:
        if not vol.get("mountpoint"):
            vol.update(VOLUME_TRANSLATIONS[volume_for])

        # Set a default LUKS volume name based on volume_for, if required.
        if vol.get("encryption") == "luks" and not vol.get("luks_volume"):
            volume_name = re.sub("_data$", "", volume_for)
            if volume_for == "postgres_tablespace":
                volume_name = vol.get("tablespace_name")
            vol["luks_volume"] = volume_name

    # We format the mountpoint so that variables like tablespace_name can be
    # incorporated into the path (see volume_translations above).
    if vol.get("mountpoint"):
        vol["mountpoint"] = vol["mountpoint"].format(v=vol)

    return vol


def find_replica_tablespace_mismatches(instances):
    """
    Returns a list of replicas whose postgres_tablespace volume definitions do not match their upstream instance.

    Args:
        instances: List of dicts for all instances in the cluster.

    """

    # First, we map instance names to a hash that tells us whether the instance
    # is a replica, who its upstream is, and what tablespace volumes it defines.
    instance_tablespaces = {}
    for i in instances:
        # We need only volume_for/tablespace_name, both of which are in
        # volumes[*].vars, so we transform the list of volumes into the
        # following list of vars.
        volume_vars = map(
            lambda vol: vol.get("vars", {}) if isinstance(vol, dict) else {},
            i.get("volumes", []),
        )

        instance_tablespaces[i["Name"]] = {
            "replica": ("replica" in i.get("role", [])),
            "upstream": i.get("upstream"),
            "tablespace_names": [
                v.get("tablespace_name")
                for v in volume_vars
                if v.get("volume_for") == "postgres_tablespace"
            ],
        }

    # For each replica, we compare its tablespace_names with its upstream's list
    # and indicate a mismatch if they are not equal.
    mismatched_replicas = []
    for name, inst in instance_tablespaces.items():
        if not inst["replica"]:
            continue

        upstream = instance_tablespaces[inst["upstream"]]
        if sorted(inst["tablespace_names"]) != sorted(upstream["tablespace_names"]):
            mismatched_replicas.append(name)

    return mismatched_replicas


def get_device_variables(volumes):
    """
    Return unique list of device variables.

    Takes a list of volumes and returns a new list where there is only one entry
    per device name (raid_device if defined, else device_name), consisting of the
    device name and any variables defined for it.

    The expanded list we start with looks like this:

    volumes:
      - raid_device: /dev/md0
        device_name: /dev/xvdf
        vars:
          mountpoint: /var/lib/postgresql
        …
      - raid_device: /dev/md0
        device_name: /dev/xvdg
        vars:
          mountpoint: /var/lib/postgresql
        …
      - device_name: /dev/xvdh
        vars:
          mountpoint: /var/lib/barman
        …

    And we end up with something like this:

    volumes:
      - device: /dev/md0
        mountpoint: /var/lib/postgresql
      - device: /dev/xvdf
        mountpoint: /var/lib/barman

    Args:
        volumes: List of volumes containing device information

    """
    seen = set()
    results = []
    for volume in volumes:
        if not isinstance(volume, dict):
            continue
        dev = volume.get("raid_device", volume.get("device_name"))
        if dev not in seen:
            seen.add(dev)
            results.append(dict(device=dev, **volume.get("vars", {})))
    return results


def export_vars(instance):
    """
    Given an instance definition, returns a dict of instance variables for the instance.

    Comprises of some instance settings (e.g., location, role, volumes), any settings mentioned in export_as_vars,
    and anything defined in vars (which takes precedence over everything else).

    For example, with the following instance definition:

    - node: 1
      xyz: 123
      pqr: 234
      location: x
      role: [a, b]
      export_as_vars:
        - xyz
        - pqr
      vars:
        abc: 345

    it would return (a superset of):

    {abc: 345, xyz: 123, pqr: 234, location: x, role: [a, b], …}

    Args:
        instance: Instance dictionary

    """
    exports = {}

    always_export = ["location"]
    for key in always_export + instance.get("export_as_vars", []):
        exports[key] = instance.get(key)

    export_if_set = ["region", "backup", "upstream"]
    for key in export_if_set:
        value = instance.get(key)
        if value is not None:
            exports[key] = value

    exports["role"] = [role for role in instance.get("role", []) if role != "postgres"]

    exports["volumes"] = get_device_variables(instance.get("volumes", []))

    exports.update(instance.get("vars", {}))

    return exports


def ensure_publication(publications, entry):
    """
    Update publications list to ensure it contains defined entry or matching replication sets.

    Modifies the given list of publications (if necessary) to ensure that the
    given publication entry occurs in it, by appending the entry if the list
    does not contain a match, or by modifying the matching entry to contain
    the desired replication sets otherwise.

    Args:
        publications: List of publications.
        entry: Entry dictionary with `type`, `database` and `replication_sets` attributes.

    """
    match = None
    for pub in publications:
        if pub["type"] == entry["type"] and pub["database"] == entry["database"]:
            match = pub

    if match:
        defined_repsets = [r["name"] for r in match["replication_sets"]]
        for repset in entry["replication_sets"]:
            if repset["name"] not in defined_repsets:
                match["replication_sets"].append(repset)
    else:
        publications.append(entry)

    return publications


def ensure_subscription(subscriptions, entry):
    """
    Update subscription list to ensure entry consistency.

    Modifies the given list of subscriptions (if necessary) to ensure that the
    given subscription entry occurs in it, by appending the entry if the list
    does not contain a match, or by modifying the matching entry to contain the
    desired replication sets otherwise.

    Args:
        subscriptions: List of subscriptions with `type` and `database` attributes
        entry: Entry dictionary with `type`, `database` and `replication_sets` attributes.

    """
    match = None
    for s in subscriptions:
        if s["type"] == entry["type"] and s["database"] == entry["database"]:
            match = s

    if match:
        # Note: For a subscription, match["replication_sets"] is just a list of
        # replication set names, not a list of structures as for publications in
        # the function above.
        for name in entry["replication_sets"]:
            if name not in match["replication_sets"]:
                match["replication_sets"].append(name)
    else:
        subscriptions.append(entry)

    return subscriptions


class FilterModule:
    def filters(self):
        return {
            "ip_addresses": ip_addresses,
            "deploy_ip_address": deploy_ip_address,
            "set_instance_defaults": set_instance_defaults,
            "expand_instance_volumes": expand_instance_volumes,
            "translate_volume_deployment_defaults": translate_volume_deployment_defaults,
            "find_replica_tablespace_mismatches": find_replica_tablespace_mismatches,
            "export_vars": export_vars,
            "ensure_publication": ensure_publication,
            "ensure_subscription": ensure_subscription,
        }
