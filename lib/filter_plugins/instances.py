#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

import copy
import re
from ansible.errors import AnsibleFilterError
from typing import List, Dict, Tuple

# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html#instance-store-volumes
#
# This table maps instance types to the number of instance store volumes
# (formerly known as ephemeral volumes) they have.
#
# Run the following command to update the contents of this table:
#
# aws ec2 describe-instance-types --output text \
#     --filters Name=instance-storage-supported,Values=true \
#     --query 'InstanceTypes[*].[InstanceType,InstanceStorageInfo.Disks[*].Count]' \
# | while read instance && read numvols; do echo "\"$instance\": $numvols,"; done
# | sed 's/^/    /'
# | sort

ephemeral_storage = {
    "c1.medium": 1,
    "c1.xlarge": 4,
    "c3.2xlarge": 2,
    "c3.4xlarge": 2,
    "c3.8xlarge": 2,
    "c3.large": 2,
    "c3.xlarge": 2,
    "c5ad.12xlarge": 2,
    "c5ad.16xlarge": 2,
    "c5ad.24xlarge": 2,
    "c5ad.2xlarge": 1,
    "c5ad.4xlarge": 2,
    "c5ad.8xlarge": 2,
    "c5ad.large": 1,
    "c5ad.xlarge": 1,
    "c5d.12xlarge": 2,
    "c5d.18xlarge": 2,
    "c5d.24xlarge": 4,
    "c5d.2xlarge": 1,
    "c5d.4xlarge": 1,
    "c5d.9xlarge": 1,
    "c5d.large": 1,
    "c5d.metal": 4,
    "c5d.xlarge": 1,
    "c6gd.12xlarge": 2,
    "c6gd.16xlarge": 2,
    "c6gd.2xlarge": 1,
    "c6gd.4xlarge": 1,
    "c6gd.8xlarge": 1,
    "c6gd.large": 1,
    "c6gd.medium": 1,
    "c6gd.metal": 2,
    "c6gd.xlarge": 1,
    "cc2.8xlarge": 4,
    "d2.2xlarge": 6,
    "d2.4xlarge": 12,
    "d2.8xlarge": 24,
    "d2.xlarge": 3,
    "d3.2xlarge": 6,
    "d3.4xlarge": 12,
    "d3.8xlarge": 24,
    "d3en.12xlarge": 24,
    "d3en.2xlarge": 4,
    "d3en.4xlarge": 8,
    "d3en.6xlarge": 12,
    "d3en.8xlarge": 16,
    "d3en.xlarge": 2,
    "d3.xlarge": 3,
    "f1.16xlarge": 4,
    "f1.2xlarge": 1,
    "f1.4xlarge": 1,
    "g2.2xlarge": 1,
    "g2.8xlarge": 2,
    "g4ad.16xlarge": 2,
    "g4ad.2xlarge": 1,
    "g4ad.4xlarge": 1,
    "g4ad.8xlarge": 1,
    "g4ad.xlarge": 1,
    "g4dn.12xlarge": 1,
    "g4dn.16xlarge": 1,
    "g4dn.2xlarge": 1,
    "g4dn.4xlarge": 1,
    "g4dn.8xlarge": 1,
    "g4dn.metal": 2,
    "g4dn.xlarge": 1,
    "h1.16xlarge": 8,
    "h1.2xlarge": 1,
    "h1.4xlarge": 2,
    "h1.8xlarge": 4,
    "i2.2xlarge": 2,
    "i2.4xlarge": 4,
    "i2.8xlarge": 8,
    "i2.xlarge": 1,
    "i3.16xlarge": 8,
    "i3.2xlarge": 1,
    "i3.4xlarge": 2,
    "i3.8xlarge": 4,
    "i3en.12xlarge": 4,
    "i3en.24xlarge": 8,
    "i3en.2xlarge": 2,
    "i3en.3xlarge": 1,
    "i3en.6xlarge": 2,
    "i3en.large": 1,
    "i3en.metal": 8,
    "i3en.xlarge": 1,
    "i3.large": 1,
    "i3.metal": 8,
    "i3.xlarge": 1,
    "m1.large": 2,
    "m1.medium": 1,
    "m1.small": 1,
    "m1.xlarge": 4,
    "m2.2xlarge": 1,
    "m2.4xlarge": 2,
    "m2.xlarge": 1,
    "m3.2xlarge": 2,
    "m3.large": 1,
    "m3.medium": 1,
    "m3.xlarge": 2,
    "m5ad.12xlarge": 2,
    "m5ad.16xlarge": 4,
    "m5ad.24xlarge": 4,
    "m5ad.2xlarge": 1,
    "m5ad.4xlarge": 2,
    "m5ad.8xlarge": 2,
    "m5ad.large": 1,
    "m5ad.xlarge": 1,
    "m5d.12xlarge": 2,
    "m5d.16xlarge": 4,
    "m5d.24xlarge": 4,
    "m5d.2xlarge": 1,
    "m5d.4xlarge": 2,
    "m5d.8xlarge": 2,
    "m5d.large": 1,
    "m5d.metal": 4,
    "m5dn.12xlarge": 2,
    "m5dn.16xlarge": 4,
    "m5dn.24xlarge": 4,
    "m5dn.2xlarge": 1,
    "m5dn.4xlarge": 2,
    "m5dn.8xlarge": 2,
    "m5dn.large": 1,
    "m5dn.metal": 4,
    "m5dn.xlarge": 1,
    "m5d.xlarge": 1,
    "m6gd.12xlarge": 2,
    "m6gd.16xlarge": 2,
    "m6gd.2xlarge": 1,
    "m6gd.4xlarge": 1,
    "m6gd.8xlarge": 1,
    "m6gd.large": 1,
    "m6gd.medium": 1,
    "m6gd.metal": 2,
    "m6gd.xlarge": 1,
    "p3dn.24xlarge": 2,
    "p4d.24xlarge": 8,
    "r3.2xlarge": 1,
    "r3.4xlarge": 1,
    "r3.8xlarge": 2,
    "r3.large": 1,
    "r3.xlarge": 1,
    "r5ad.12xlarge": 2,
    "r5ad.16xlarge": 4,
    "r5ad.24xlarge": 4,
    "r5ad.2xlarge": 1,
    "r5ad.4xlarge": 2,
    "r5ad.8xlarge": 2,
    "r5ad.large": 1,
    "r5ad.xlarge": 1,
    "r5d.12xlarge": 2,
    "r5d.16xlarge": 4,
    "r5d.24xlarge": 4,
    "r5d.2xlarge": 1,
    "r5d.4xlarge": 2,
    "r5d.8xlarge": 2,
    "r5d.large": 1,
    "r5d.metal": 4,
    "r5dn.12xlarge": 2,
    "r5dn.16xlarge": 4,
    "r5dn.24xlarge": 4,
    "r5dn.2xlarge": 1,
    "r5dn.4xlarge": 2,
    "r5dn.8xlarge": 2,
    "r5dn.large": 1,
    "r5dn.metal": 4,
    "r5dn.xlarge": 1,
    "r5d.xlarge": 1,
    "r6gd.12xlarge": 2,
    "r6gd.16xlarge": 2,
    "r6gd.2xlarge": 1,
    "r6gd.4xlarge": 1,
    "r6gd.8xlarge": 1,
    "r6gd.large": 1,
    "r6gd.medium": 1,
    "r6gd.metal": 2,
    "r6gd.xlarge": 1,
    "x1.16xlarge": 1,
    "x1.32xlarge": 2,
    "x1e.16xlarge": 1,
    "x1e.2xlarge": 1,
    "x1e.32xlarge": 2,
    "x1e.4xlarge": 1,
    "x1e.8xlarge": 1,
    "x1e.xlarge": 1,
    "x2gd.12xlarge": 2,
    "x2gd.16xlarge": 2,
    "x2gd.2xlarge": 1,
    "x2gd.4xlarge": 1,
    "x2gd.8xlarge": 1,
    "x2gd.large": 1,
    "x2gd.medium": 1,
    "x2gd.metal": 2,
    "x2gd.xlarge": 1,
    "z1d.12xlarge": 2,
    "z1d.2xlarge": 1,
    "z1d.3xlarge": 1,
    "z1d.6xlarge": 1,
    "z1d.large": 1,
    "z1d.metal": 2,
    "z1d.xlarge": 1,
}

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

    def merged_defaults(item, defaults, omit_keys=[]):
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
                location = locations[location]
            elif location in locations_map:
                location = locations_map[location]
            else:
                raise AnsibleFilterError(
                    "Instance %s specifies unknown location %s" % (j["Name"], location)
                )

            j.update(merged_defaults(j, location, omit_keys=["Name"]))

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


# This filter sets the image for each instance, if not already specified.


def expand_instance_image(old_instances, ec2_region_amis):
    instances = []

    for i in old_instances:
        j = copy.deepcopy(i)

        if "image" not in j:
            j["image"] = ec2_region_amis[j["region"]]

        instances.append(j)

    return instances


# This filter translates a device name of 'root' to the given root
# device name, and sets delete_on_termination to true if it's not
# implied by attach_existing or explicitly set to be false.


def expand_instance_volumes(old_instances, ec2_ami_properties):
    instances = []

    for i in old_instances:
        j = copy.deepcopy(i)

        volumes = []
        for vol in j.get("volumes", []):
            v = copy.deepcopy(vol)
            vars = v.get("vars", {})

            volume_type = v.get("volume_type")
            if volume_type == "none":
                continue

            if not (volume_type or "ephemeral" in v):
                raise AnsibleFilterError(
                    "volume_type/ephemeral not specified for volume %s"
                    % (v["device_name"])
                )

            if v["device_name"] == "root":
                v["device_name"] = ec2_ami_properties[j["image"]]["root_device_name"]
                if "mountpoint" in vars or "volume_for" in vars:
                    raise AnsibleFilterError(
                        "root volume cannot have mountpoint/volume_for set"
                    )
            if not "delete_on_termination" in v:
                v["delete_on_termination"] = not v.get("attach_existing", False)

            validate_volume_for(v["device_name"], vars)

            volumes.append(v)

            # If the entry specifies raid_device, then we repeat this volume
            # raid_units-1 times.

            if "raid_device" in v:
                n = v["raid_units"]

                if n == "all":
                    if "ephemeral" in v:
                        if i["type"] in ephemeral_storage:
                            n = ephemeral_storage[i["type"]]
                        else:
                            raise AnsibleFilterError(
                                "ephemeral storage unavailable for %s" % i["type"]
                            )
                    else:
                        raise AnsibleFilterError(
                            "raid_units=all can be used only with ephemeral storage"
                        )
                n -= 1

                vn = v
                while n > 0:
                    vn = copy.deepcopy(vn)

                    name = vn["device_name"]
                    vn["device_name"] = name[0:-1] + chr(ord(name[-1]) + 1)

                    if "ephemeral" in vn:
                        ename = vn["ephemeral"]
                        vn["ephemeral"] = ename[0:-1] + chr(ord(ename[-1]) + 1)

                    volumes.append(vn)
                    n -= 1

        j["volumes"] = volumes
        instances.append(j)

    return instances


volume_translations = {
    "barman_data": {"mountpoint": "/var/lib/barman"},
    "postgres_data": {"mountpoint": "/opt/postgres"},
    "postgres_wal": {"mountpoint": "/opt/postgres/wal"},
    "postgres_tablespace": {
        "mountpoint": "/opt/postgres/tablespaces/{v[tablespace_name]}"
    },
}


def validate_volume_for(device_name, vars) -> None:
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
    volume_for = vars.get("volume_for")
    if volume_for and volume_for not in volume_translations:
        raise AnsibleFilterError(
            "volume %s has unrecognised volume_for=%s" % (device_name, volume_for)
        )

    if volume_for == "postgres_tablespace" and not vars.get("tablespace_name"):
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
        volume_vars = map(lambda vol: vol.get("vars", {}), i.get("volumes", []))

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
            vars = v.get("vars", {})
            results.append(dict(device=dev, **vars))
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


class FilterModule(object):
    def filters(self):
        return {
            "ip_addresses": ip_addresses,
            "deploy_ip_address": deploy_ip_address,
            "set_instance_defaults": set_instance_defaults,
            "expand_instance_image": expand_instance_image,
            "expand_instance_volumes": expand_instance_volumes,
            "translate_volume_deployment_defaults": translate_volume_deployment_defaults,
            "find_replica_tablespace_mismatches": find_replica_tablespace_mismatches,
            "match_existing_volumes": match_existing_volumes,
            "export_vars": export_vars,
        }
