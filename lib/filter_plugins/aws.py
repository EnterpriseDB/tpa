#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.
#
"""AWS platform specific filters."""

import copy

from ansible.errors import AnsibleFilterError

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
# | jq '.[]|{(.[0]):.[1][0]}' | jq -s add
EPHEMERAL_STORAGE = {
    "x2gd.8xlarge": 1,
    "m5dn.2xlarge": 1,
    "x1e.2xlarge": 1,
    "x1e.8xlarge": 1,
    "g5.2xlarge": 1,
    "im4gn.8xlarge": 2,
    "r6gd.2xlarge": 1,
    "im4gn.2xlarge": 1,
    "x2iedn.xlarge": 1,
    "m6gd.4xlarge": 1,
    "is4gen.xlarge": 1,
    "m2.4xlarge": 2,
    "d3en.8xlarge": 16,
    "i2.2xlarge": 2,
    "m5d.8xlarge": 2,
    "c5ad.12xlarge": 2,
    "c5d.large": 1,
    "d3en.2xlarge": 4,
    "x1.16xlarge": 1,
    "r6gd.medium": 1,
    "g5.4xlarge": 1,
    "m5ad.4xlarge": 2,
    "c5ad.24xlarge": 2,
    "m6gd.medium": 1,
    "r5ad.24xlarge": 4,
    "m5ad.large": 1,
    "i3en.3xlarge": 1,
    "m5d.xlarge": 1,
    "r5dn.8xlarge": 2,
    "c6gd.metal": 2,
    "z1d.2xlarge": 1,
    "m5dn.12xlarge": 2,
    "m6gd.12xlarge": 2,
    "c5d.12xlarge": 2,
    "is4gen.4xlarge": 2,
    "m6gd.xlarge": 1,
    "m5dn.large": 1,
    "x2gd.metal": 2,
    "x2iedn.2xlarge": 1,
    "x1e.32xlarge": 2,
    "c3.large": 2,
    "c5ad.4xlarge": 2,
    "r3.large": 1,
    "d2.8xlarge": 24,
    "i3en.12xlarge": 4,
    "r3.8xlarge": 2,
    "f1.2xlarge": 1,
    "i3en.24xlarge": 8,
    "m5ad.12xlarge": 2,
    "r6gd.xlarge": 1,
    "c3.8xlarge": 2,
    "g5.24xlarge": 1,
    "m2.2xlarge": 1,
    "h1.8xlarge": 4,
    "z1d.xlarge": 1,
    "c5d.24xlarge": 4,
    "d2.2xlarge": 6,
    "x2gd.4xlarge": 1,
    "m6gd.metal": 2,
    "m5dn.8xlarge": 2,
    "m5d.16xlarge": 4,
    "c1.xlarge": 4,
    "m5ad.2xlarge": 1,
    "d3.8xlarge": 24,
    "r6gd.large": 1,
    "g2.2xlarge": 1,
    "r5dn.xlarge": 1,
    "c5ad.xlarge": 1,
    "g4ad.2xlarge": 1,
    "x2idn.24xlarge": 2,
    "d3.xlarge": 3,
    "g4ad.8xlarge": 1,
    "c1.medium": 1,
    "g4ad.4xlarge": 1,
    "r5ad.12xlarge": 2,
    "g4dn.12xlarge": 1,
    "m6gd.16xlarge": 2,
    "m5d.large": 1,
    "m5ad.8xlarge": 2,
    "r6gd.metal": 2,
    "r5ad.8xlarge": 2,
    "g4dn.metal": 2,
    "c5d.2xlarge": 1,
    "r5d.4xlarge": 2,
    "im4gn.xlarge": 1,
    "m5d.metal": 4,
    "x2gd.16xlarge": 2,
    "m5dn.xlarge": 1,
    "d3en.4xlarge": 8,
    "c6gd.16xlarge": 2,
    "c5ad.16xlarge": 2,
    "x2gd.medium": 1,
    "h1.4xlarge": 2,
    "r5d.xlarge": 1,
    "g5.12xlarge": 1,
    "r5d.large": 1,
    "m5ad.24xlarge": 4,
    "m5d.24xlarge": 4,
    "c5ad.2xlarge": 1,
    "m3.xlarge": 2,
    "x2gd.12xlarge": 2,
    "i2.xlarge": 1,
    "c3.xlarge": 2,
    "x2idn.16xlarge": 1,
    "i3.xlarge": 1,
    "m1.xlarge": 4,
    "p4d.24xlarge": 8,
    "r5d.2xlarge": 1,
    "x2gd.xlarge": 1,
    "r5ad.2xlarge": 1,
    "r5d.8xlarge": 2,
    "r5dn.large": 1,
    "d3en.6xlarge": 12,
    "d3.2xlarge": 6,
    "h1.16xlarge": 8,
    "r5ad.large": 1,
    "is4gen.2xlarge": 1,
    "x2iedn.4xlarge": 1,
    "x2gd.2xlarge": 1,
    "r3.2xlarge": 1,
    "h1.2xlarge": 1,
    "r5dn.metal": 4,
    "c6gd.xlarge": 1,
    "m5dn.metal": 4,
    "c5d.18xlarge": 2,
    "g5.16xlarge": 1,
    "r6gd.4xlarge": 1,
    "r3.xlarge": 1,
    "r5d.16xlarge": 4,
    "r5d.24xlarge": 4,
    "r3.4xlarge": 1,
    "c5d.4xlarge": 1,
    "r5dn.2xlarge": 1,
    "i3en.large": 1,
    "x1e.xlarge": 1,
    "z1d.metal": 2,
    "d2.4xlarge": 12,
    "x2idn.32xlarge": 2,
    "x2iedn.16xlarge": 1,
    "i2.8xlarge": 8,
    "x1e.16xlarge": 1,
    "g5.xlarge": 1,
    "m6gd.8xlarge": 1,
    "im4gn.16xlarge": 4,
    "r6gd.16xlarge": 2,
    "m5dn.4xlarge": 2,
    "im4gn.large": 1,
    "c3.2xlarge": 2,
    "m5dn.16xlarge": 4,
    "c5d.xlarge": 1,
    "c6gd.medium": 1,
    "x2gd.large": 1,
    "c5ad.8xlarge": 2,
    "m5d.2xlarge": 1,
    "g4ad.16xlarge": 2,
    "r5ad.16xlarge": 4,
    "x2iedn.24xlarge": 2,
    "m5ad.xlarge": 1,
    "r5d.metal": 4,
    "r5ad.4xlarge": 2,
    "r5ad.xlarge": 1,
    "m5d.12xlarge": 2,
    "i3.8xlarge": 4,
    "is4gen.large": 1,
    "r5dn.16xlarge": 4,
    "i3.large": 1,
    "c3.4xlarge": 2,
    "r6gd.8xlarge": 1,
    "i3en.2xlarge": 2,
    "im4gn.4xlarge": 1,
    "z1d.6xlarge": 1,
    "i3en.xlarge": 1,
    "z1d.12xlarge": 2,
    "z1d.large": 1,
    "d3.4xlarge": 12,
    "i2.4xlarge": 4,
    "c5d.metal": 4,
    "r5dn.12xlarge": 2,
    "m5dn.24xlarge": 4,
    "m5ad.16xlarge": 4,
    "g4dn.16xlarge": 1,
    "i3.16xlarge": 8,
    "g4dn.xlarge": 1,
    "m3.2xlarge": 2,
    "i3.2xlarge": 1,
    "f1.4xlarge": 1,
    "p3dn.24xlarge": 2,
    "i3en.6xlarge": 2,
    "i3en.metal": 8,
    "c6gd.2xlarge": 1,
    "m1.large": 2,
    "g5.48xlarge": 2,
    "g4dn.8xlarge": 1,
    "m1.medium": 1,
    "m2.xlarge": 1,
    "m6gd.large": 1,
    "x1.32xlarge": 2,
    "g2.8xlarge": 2,
    "c6gd.4xlarge": 1,
    "i3.4xlarge": 2,
    "cc2.8xlarge": 4,
    "g5.8xlarge": 1,
    "r5dn.24xlarge": 4,
    "is4gen.8xlarge": 4,
    "m1.small": 1,
    "m3.large": 1,
    "m3.medium": 1,
    "c6gd.8xlarge": 1,
    "x2iedn.8xlarge": 1,
    "c6gd.large": 1,
    "m6gd.2xlarge": 1,
    "d3en.xlarge": 2,
    "x1e.4xlarge": 1,
    "d2.xlarge": 3,
    "c5ad.large": 1,
    "g4dn.2xlarge": 1,
    "c6gd.12xlarge": 2,
    "r5dn.4xlarge": 2,
    "g4ad.xlarge": 1,
    "r5d.12xlarge": 2,
    "z1d.3xlarge": 1,
    "m5d.4xlarge": 2,
    "x2iedn.32xlarge": 2,
    "d3en.12xlarge": 24,
    "c5d.9xlarge": 1,
    "is4gen.medium": 1,
    "i3.metal": 8,
    "g4dn.4xlarge": 1,
    "r6gd.12xlarge": 2,
    "f1.16xlarge": 4,
}


def expand_ec2_instance_image(old_instances, ec2_region_amis):
    """Filter to set the image for each instance, if not already specified."""
    instances = []

    for i in old_instances:
        j = copy.deepcopy(i)

        if "image" not in j:
            j["image"] = ec2_region_amis[j["region"]]

        instances.append(j)

    return instances


def expand_ec2_instance_volumes(old_instances, ec2_ami_properties):
    """
    Expand the instance volume list according to a set of AWS specific transformations.

    Operations performed:
    * translates a device name of 'root' to the given root device name
    * sets delete_on_termination to true if it's not implied by attach_existing or explicitly set to be false.
    * Configures RAID devices

    """
    instances = []

    for instance in old_instances:
        transform = copy.deepcopy(instance)

        volumes = []
        for vol in transform.get("volumes", []):
            volume = copy.deepcopy(vol)
            _vars = volume.get("vars", {})

            volume_type = volume.get("volume_type")

            if not (volume_type or "ephemeral" in volume):
                raise AnsibleFilterError(
                    f"volume_type/ephemeral not specified for volume {volume['device_name']}"
                )

            if volume["device_name"] == "root":
                volume["device_name"] = ec2_ami_properties[transform["image"]][
                    "root_device_name"
                ]
                if "mountpoint" in _vars or "volume_for" in _vars:
                    raise AnsibleFilterError(
                        "root volume cannot have mountpoint/volume_for set"
                    )
            if "delete_on_termination" not in volume:
                volume["delete_on_termination"] = not volume.get(
                    "attach_existing", False
                )

            volumes.append(volume)

            update_raid_volumes(volume, volumes, instance)

        transform["volumes"] = volumes
        instances.append(transform)

    return instances


def update_raid_volumes(volume, volumes, instance=None):
    """
    If the entry specifies raid_device, then we repeat this volume raid_units-1 times.

    Args:
        volume: Volume dict containing raid_device information (skipped if missing)
        volumes: List of existing volumes
        instance: instance dict for checking ephemeral storage type.

    """
    if "raid_device" in volume:
        raid_units = volume["raid_units"]

        if raid_units == "all":
            if "ephemeral" in volume:
                if instance and instance.get("type") in EPHEMERAL_STORAGE:
                    raid_units = EPHEMERAL_STORAGE[instance["type"]]
                else:
                    raise AnsibleFilterError(
                        f"ephemeral storage unavailable for {instance['type']}"
                    )
            else:
                raise AnsibleFilterError(
                    "raid_units=all can be used only with ephemeral storage"
                )
        raid_units -= 1

        raid_volume = volume
        while raid_units > 0:
            raid_volume = copy.deepcopy(raid_volume)

            name = raid_volume["device_name"]
            raid_volume["device_name"] = name[0:-1] + chr(ord(name[-1]) + 1)

            if "ephemeral" in raid_volume:
                ename = raid_volume["ephemeral"]
                raid_volume["ephemeral"] = ename[0:-1] + chr(ord(ename[-1]) + 1)

            volumes.append(raid_volume)
            raid_units -= 1


def match_existing_volumes(old_instances, cluster_name, ec2_volumes=None):
    """
    Filter to set the volume_id for any volumes that match existing attachable volumes as discovered by a tag search.

    Args:
        old_instances: List of instances containing volumes lists to update to existing volumes
        cluster_name: Name of the cluster
        ec2_volumes: List of existing ec2 volumes found

    """
    instances = []
    ec2_volumes = ec2_volumes or {}
    for instance in old_instances:
        for volume in instance.get("volumes", []):
            if not volume.get("attach_existing", False):
                continue

            name = ":".join(
                [
                    instance["region"],
                    cluster_name,
                    str(instance["node"]),
                    volume["device_name"],
                ]
            )
            if name in ec2_volumes:
                ec2_volume = ec2_volumes[name]

                if (
                    volume["volume_size"] != ec2_volume["size"]
                    or volume.get("iops", ec2_volume["iops"]) != ec2_volume["iops"]
                    or volume.get("volume_type", ec2_volume["type"])
                    != ec2_volume["type"]
                ):
                    continue

                volume["volume_id"] = ec2_volume["id"]

        instances.append(instance)

    return instances


class FilterModule:
    def filters(self):
        return {
            "expand_ec2_instance_image": expand_ec2_instance_image,
            "expand_ec2_instance_volumes": expand_ec2_instance_volumes,
            "match_existing_volumes": match_existing_volumes,
        }
