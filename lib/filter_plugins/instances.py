#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import copy
import re
from ansible.errors import AnsibleFilterError


## Instance filters
#
# The filters defined here take the array of instances (from config.yml)
# and other inputs and return a new array of instances with parameters
# suitably adjusted.

# Returns a hash of the IP addresses specified for a given instance.


def ip_addresses(instance):
    addresses = {}

    for a in ["ip_address", "public_ip", "private_ip"]:
        ip = instance.get(a)
        if ip is not None:
            addresses[a] = ip

    return addresses


# Returns the IP address that TPAexec should use to ssh to an instance. The
# public_ip, ip_address, and private_ip are used in order of decreasing
# preference.


def deploy_ip_address(instance):
    return (
        instance.get("public_ip")
        or instance.get("ip_address")
        or instance.get("private_ip")
    )


# Every instance must have certain settings (e.g., tags) in a specific format.


def set_instance_defaults(old_instances, cluster_name, instance_defaults, locations):
    instances = []

    locations_map = {}
    for l in locations:
        locations_map[l["Name"]] = l

    # Returns a mapping with the keys in defaults (excluding those given in
    # omit_keys) and the corresponding values from item (if specified) or from
    # defaults otherwise. Any dict values are further merged for convenience, so
    # that defaults can specify some keys and item can override or extend them.

    def merged_defaults(item, defaults, omit_keys=None):
        omit_keys = omit_keys or []
        result = {}

        for key in [k for k in defaults if k not in omit_keys]:
            result[key] = item.get(key, defaults[key])
            if isinstance(result[key], dict) and isinstance(defaults[key], dict):
                b = copy.deepcopy(defaults[key])
                b.update(result[key])
                result[key] = b

        return result

    for i in old_instances:
        j = copy.deepcopy(i)
        tags = j.get("tags", {})

        # Every instance must have a sensible name (lowercase, without
        # underscores). If it's set under .tags, we'll move it up.

        name = j.get("Name", tags.get("Name", None))
        if name is None:
            name = cluster_name + "-" + str(j["node"])
        j["Name"] = name.replace("_", "-").lower()
        j["vars"] = j.get("vars", {})

        # Anything set in instance_defaults should be copied to the instance,
        # unless the instance has a setting that overrides the default. As a
        # convenience, we also merge dict keys (so that once can, for example,
        # set some vars in instance_defaults and some on the instance, and get
        # all of them, with the instance settings overriding the defaults).

        j.update(merged_defaults(j, instance_defaults, omit_keys=["default_volumes"]))

        # If instance_defaults specifies 'default_volumes', we merge those
        # entries with the instance's 'volumes', with entries in the latter
        # taking precedence over default entries with the same device name.
        # (Setting 'volumes' to [] explicitly in instances will remove the
        # defaults altogether.)

        volumes = j.get("volumes", [])
        default_volumes = instance_defaults.get("default_volumes", [])
        if default_volumes and (len(volumes) > 0 or "volumes" not in j):
            volume_map = {}
            for vol in default_volumes + volumes:
                name = vol.get("raid_device", vol.get("device_name"))
                if name.startswith("/dev/"):
                    name = name[5:]
                volume_map[name] = vol

            volumes = []
            for name in sorted(volume_map.keys()):
                volumes.append(volume_map[name])

            j["volumes"] = volumes

        # If the instance specifies «location: x», where x is either a name or
        # an array index (for backwards compatibility), we copy the settings
        # from location x to the instance, in exactly the same way as we do
        # above for instance_defaults.

        location = j.get("location", None)
        if len(locations) > 0 and location is not None:
            if isinstance(location, int) and location < len(locations):
                location_defaults = locations[location]
                j['location'] = locations[location]['Name']
            elif location in locations_map:
                location_defaults = locations_map[location]
            else:
                raise AnsibleFilterError(
                    "Instance %s specifies unknown location %s" % (j["Name"], location)
                )

            j.update(merged_defaults(j, location_defaults, omit_keys=["Name"]))

        # The upstream, backup, and role tags should be moved one level up if
        # they're specified at all.

        for t in ["upstream", "backup", "role"]:
            if t in tags:
                j[t] = tags[t]
                del tags[t]

        # The role tag should be a list, so we convert comma-separated
        # strings if that's what we're given.

        role = j.get("role", [])
        if not isinstance(role, list):
            role = [x.strip() for x in role.split(",")]

        # primary/replica instances must also be tagged 'postgres'.

        if "primary" in role or "replica" in role:
            if "postgres" not in role:
                role = role + ["postgres"]

        j["role"] = role
        j["tags"] = tags

        # Name and node should be in tags, but we'll add them in when we're
        # actually creating the tags, not before.

        for t in ["name", "Name", "node"]:
            if t in tags:
                del tags[t]

        instances.append(j)

    return instances


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


volume_translations = {
    "barman_data": {"mountpoint": "/var/lib/barman"},
    "postgres_data": {"mountpoint": "/opt/postgres"},
    "postgres_wal": {"mountpoint": "/opt/postgres/wal"},
    "postgres_tablespace": {
        "mountpoint": "/opt/postgres/tablespaces/{v[tablespace_name]}"
    },
}


def validate_volume_for(device_name, _vars) -> None:
    """
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
    if volume_for and volume_for not in volume_translations:
        raise AnsibleFilterError(
            "volume %s has unrecognised volume_for=%s" % (device_name, volume_for)
        )

    if volume_for == "postgres_tablespace" and not _vars.get("tablespace_name"):
        raise AnsibleFilterError(
            "volume %s is %s; must define tablespace_name" % (device_name, volume_for)
        )


def translate_volume_deployment_defaults(vol):
    """
    Modifies the given entry from `volumes` in the inventory to translate its
    volume_for into a mountpoint and other volume defaults if needed. Meant to
    be used only as a |map function.

    See roles/platforms/common/tasks/volumes.yml for more details.
    """
    validate_volume_for(vol["device"], vol)

    # If we have a valid volume_for, we can translate that into a default
    # mountpoint (unless one is explicitly set).
    volume_for = vol.get("volume_for")
    if volume_for:
        if not vol.get("mountpoint"):
            vol.update(volume_translations[volume_for])

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
    Given a list of all instances, returns a list of replicas whose
    postgres_tablespace volume definitions do not match the volume definitions
    on their upstream instance.
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
    for Name, inst in instance_tablespaces.items():
        if not inst["replica"]:
            continue

        upstream = instance_tablespaces[inst["upstream"]]
        if sorted(inst["tablespace_names"]) != sorted(upstream["tablespace_names"]):
            mismatched_replicas.append(Name)

    return mismatched_replicas


# This filter sets the volume_id for any volumes that match existing attachable
# volumes as discovered by a tag search.


def match_existing_volumes(old_instances, cluster_name, ec2_volumes):
    instances = []

    for i in old_instances:
        for v in i.get("volumes", []):
            if not v.get("attach_existing", False):
                continue

            name = ":".join(
                [i["region"], cluster_name, str(i["node"]), v["device_name"]]
            )
            if name in ec2_volumes:
                ev = ec2_volumes[name]

                if (
                    v["volume_size"] != ev["size"]
                    or v.get("iops", ev["iops"]) != ev["iops"]
                    or v.get("volume_type", ev["type"]) != ev["type"]
                ):
                    continue

                v["volume_id"] = ev["id"]

        instances.append(i)

    return instances


# Takes a list of volumes and returns a new list where there is only one entry
# per device name (raid_device if defined, else device_name), consisting of the
# device name and any variables defined for it.
#
# The expanded list we start with looks like this:
#
# volumes:
#   - raid_device: /dev/md0
#     device_name: /dev/xvdf
#     vars:
#       mountpoint: /var/lib/postgresql
#     …
#   - raid_device: /dev/md0
#     device_name: /dev/xvdg
#     vars:
#       mountpoint: /var/lib/postgresql
#     …
#   - device_name: /dev/xvdh
#     vars:
#       mountpoint: /var/lib/barman
#     …
#
# And we end up with something like this:
#
# volumes:
#   - device: /dev/md0
#     mountpoint: /var/lib/postgresql
#   - device: /dev/xvdf
#     mountpoint: /var/lib/barman


def get_device_variables(volumes):
    seen = set()
    results = []
    for v in volumes:
        if not isinstance(v, dict):
            continue
        dev = v.get("raid_device", v.get("device_name"))
        if dev not in seen:
            seen.add(dev)
            results.append(dict(device=dev, **v.get("vars", {})))
    return results


# Given an instance definition, returns a dict of instance variables for the
# instance, comprising some instance settings (e.g., location, role, volumes),
# any settings mentioned in export_as_vars, and anything defined in vars (which
# takes precedence over everything else).
#
# For example, with the following instance definition:
#
# - node: 1
#   xyz: 123
#   pqr: 234
#   location: x
#   role: [a, b]
#   export_as_vars:
#     - xyz
#     - pqr
#   vars:
#     abc: 345
#
# it would return (a superset of):
#
# {abc: 345, xyz: 123, pqr: 234, location: x, role: [a, b], …}


def export_vars(instance):
    exports = {}

    always_export = ["location"]
    for k in always_export + instance.get("export_as_vars", []):
        exports[k] = instance.get(k)

    export_if_set = ["region", "backup", "upstream"]
    for k in export_if_set:
        v = instance.get(k)
        if v is not None:
            exports[k] = v

    exports["role"] = [x for x in instance.get("role", []) if x != "postgres"]

    exports["volumes"] = get_device_variables(instance.get("volumes", []))

    exports.update(instance.get("vars", {}))

    return exports


def ensure_publication(publications, entry):
    """
    Modifies the given list of publications (if necessary) to ensure that the
    given publication entry occurs in it, by appending the entry if the list
    does not contain a match, or by modifying the matching entry to contain
    the desired replication sets otherwise.
    """
    match = None
    for p in publications:
        if p["type"] == entry["type"] and p["database"] == entry["database"]:
            match = p

    if match:
        defined_repsets = [r["name"] for r in match["replication_sets"]]
        for r in entry["replication_sets"]:
            if r["name"] not in defined_repsets:
                match["replication_sets"].append(r)
    else:
        publications.append(entry)

    return publications


def ensure_subscription(subscriptions, entry):
    """
    Modifies the given list of subscriptions (if necessary) to ensure that the
    given subscription entry occurs in it, by appending the entry if the list
    does not contain a match, or by modifying the matching entry to contain the
    desired replication sets otherwise.
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


class FilterModule(object):
    def filters(self):
        return {
            "ip_addresses": ip_addresses,
            "deploy_ip_address": deploy_ip_address,
            "set_instance_defaults": set_instance_defaults,
            "expand_instance_volumes": expand_instance_volumes,
            "translate_volume_deployment_defaults": translate_volume_deployment_defaults,
            "find_replica_tablespace_mismatches": find_replica_tablespace_mismatches,
            "match_existing_volumes": match_existing_volumes,
            "export_vars": export_vars,
            "ensure_publication": ensure_publication,
            "ensure_subscription": ensure_subscription,
        }
