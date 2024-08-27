#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.
#
"""AWS platform specific filters."""

import copy

from filter_plugins.instances import export_vars

from ansible.errors import AnsibleFilterError

# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html#instance-store-volumes
#
# This table maps instance types to the number of instance store volumes
# (formerly known as ephemeral volumes) they have.
#
# Run the following command to update the contents of this table:
#
# aws ec2 --region us-west-1 describe-instance-types \
#        --filters "Name=instance-storage-supported,Values=true" \
#        --query "InstanceTypes[].[InstanceType, InstanceStorageInfo.Disks[*].{storage_count: Count}]"
#        --output json | jq '.[]|{(.[0]):.[1][0]["storage_count"]}' | jq -s add
#
EPHEMERAL_STORAGE = {
  "x2gd.8xlarge": 1,
  "x1e.8xlarge": 1,
  "i2.2xlarge": 2,
  "c6id.8xlarge": 1,
  "m6idn.large": 1,
  "m5ad.12xlarge": 2,
  "x1e.2xlarge": 1,
  "m6gd.xlarge": 1,
  "m7gd.xlarge": 1,
  "m5dn.large": 1,
  "m5d.8xlarge": 2,
  "i3en.12xlarge": 4,
  "m5dn.12xlarge": 2,
  "g6.24xlarge": 4,
  "m7gd.16xlarge": 2,
  "x2gd.metal": 2,
  "r5dn.8xlarge": 2,
  "c5d.large": 1,
  "r6idn.16xlarge": 2,
  "i3en.3xlarge": 1,
  "m7gd.large": 1,
  "c6gd.metal": 2,
  "im4gn.2xlarge": 1,
  "m5dn.2xlarge": 1,
  "c3.8xlarge": 2,
  "i4i.16xlarge": 4,
  "g5.2xlarge": 1,
  "m5d.xlarge": 1,
  "m6id.2xlarge": 1,
  "is4gen.4xlarge": 2,
  "m6id.xlarge": 1,
  "m2.4xlarge": 2,
  "r6gd.medium": 1,
  "trn1.32xlarge": 4,
  "r3.large": 1,
  "r6gd.2xlarge": 1,
  "c7gd.medium": 1,
  "c3.large": 2,
  "i3en.24xlarge": 8,
  "is4gen.xlarge": 1,
  "x2iedn.2xlarge": 1,
  "m6gd.12xlarge": 2,
  "d3en.2xlarge": 4,
  "m6gd.4xlarge": 1,
  "f1.2xlarge": 1,
  "g5.4xlarge": 1,
  "r6id.16xlarge": 2,
  "c5ad.24xlarge": 2,
  "i4g.xlarge": 1,
  "r5ad.8xlarge": 2,
  "m6idn.4xlarge": 1,
  "r5ad.24xlarge": 4,
  "r3.8xlarge": 2,
  "d3en.8xlarge": 16,
  "x2idn.24xlarge": 2,
  "m6id.12xlarge": 2,
  "i4i.24xlarge": 6,
  "d2.8xlarge": 24,
  "r6idn.2xlarge": 1,
  "c5ad.12xlarge": 2,
  "r6gd.large": 1,
  "c5ad.4xlarge": 2,
  "m6id.32xlarge": 4,
  "m5dn.xlarge": 1,
  "r6idn.xlarge": 1,
  "m5ad.4xlarge": 2,
  "r6id.4xlarge": 1,
  "r6gd.xlarge": 1,
  "c5d.12xlarge": 2,
  "r7gd.8xlarge": 1,
  "x1e.32xlarge": 2,
  "r7gd.xlarge": 1,
  "x1.16xlarge": 1,
  "r5ad.12xlarge": 2,
  "trn1.2xlarge": 1,
  "m6gd.medium": 1,
  "r6idn.24xlarge": 4,
  "m6idn.12xlarge": 2,
  "m5ad.large": 1,
  "g4dn.metal": 2,
  "r6id.12xlarge": 2,
  "z1d.2xlarge": 1,
  "trn1n.32xlarge": 4,
  "im4gn.8xlarge": 2,
  "r6id.2xlarge": 1,
  "c6id.24xlarge": 4,
  "im4gn.xlarge": 1,
  "r6idn.8xlarge": 1,
  "x2iedn.xlarge": 1,
  "r6id.xlarge": 1,
  "i4g.8xlarge": 2,
  "i4i.4xlarge": 1,
  "g6.8xlarge": 2,
  "i4i.metal": 8,
  "x2gd.16xlarge": 2,
  "c5ad.16xlarge": 2,
  "g4ad.2xlarge": 1,
  "c7gd.16xlarge": 2,
  "c6id.16xlarge": 2,
  "m5d.metal": 4,
  "h1.8xlarge": 4,
  "c5ad.xlarge": 1,
  "g4dn.12xlarge": 1,
  "x2gd.4xlarge": 1,
  "g4ad.4xlarge": 1,
  "m5dn.8xlarge": 2,
  "c5d.2xlarge": 1,
  "m7gd.12xlarge": 2,
  "c6id.large": 1,
  "m5d.large": 1,
  "m5d.16xlarge": 4,
  "m5ad.2xlarge": 1,
  "g5.24xlarge": 1,
  "r7gd.16xlarge": 2,
  "d3.8xlarge": 24,
  "r6gd.metal": 2,
  "d2.2xlarge": 6,
  "m6gd.metal": 2,
  "m2.2xlarge": 1,
  "c1.xlarge": 4,
  "i4g.large": 1,
  "g6.48xlarge": 8,
  "m5ad.8xlarge": 2,
  "z1d.xlarge": 1,
  "g4ad.8xlarge": 1,
  "x2gd.medium": 1,
  "x2iedn.metal": 2,
  "i4i.2xlarge": 1,
  "g5.12xlarge": 1,
  "c7gd.xlarge": 1,
  "c1.medium": 1,
  "r5dn.large": 1,
  "x2gd.xlarge": 1,
  "c5d.4xlarge": 1,
  "d3.2xlarge": 6,
  "r5d.large": 1,
  "m7gd.metal": 2,
  "c6gd.xlarge": 1,
  "r6id.24xlarge": 4,
  "m7gd.medium": 1,
  "r5dn.xlarge": 1,
  "m6gd.16xlarge": 2,
  "r5ad.large": 1,
  "r3.4xlarge": 1,
  "r6id.32xlarge": 4,
  "h1.2xlarge": 1,
  "i4g.4xlarge": 1,
  "c5d.24xlarge": 4,
  "r7gd.medium": 1,
  "r6gd.4xlarge": 1,
  "m6idn.xlarge": 1,
  "r3.2xlarge": 1,
  "c7gd.large": 1,
  "d3en.4xlarge": 8,
  "p4d.24xlarge": 8,
  "r5d.xlarge": 1,
  "m1.xlarge": 4,
  "r5dn.metal": 4,
  "m7gd.8xlarge": 1,
  "d3.xlarge": 3,
  "d3en.6xlarge": 12,
  "x2gd.2xlarge": 1,
  "c3.xlarge": 2,
  "c6gd.16xlarge": 2,
  "m3.xlarge": 2,
  "i4g.2xlarge": 1,
  "r5d.4xlarge": 2,
  "m6idn.32xlarge": 4,
  "i4g.16xlarge": 4,
  "i4i.large": 1,
  "r7gd.4xlarge": 1,
  "is4gen.2xlarge": 1,
  "r6idn.4xlarge": 1,
  "c5ad.2xlarge": 1,
  "m6idn.2xlarge": 1,
  "m5d.24xlarge": 4,
  "m6id.16xlarge": 2,
  "r7gd.large": 1,
  "h1.4xlarge": 2,
  "r3.xlarge": 1,
  "m7gd.4xlarge": 1,
  "g5.16xlarge": 1,
  "m5ad.24xlarge": 4,
  "r5d.24xlarge": 4,
  "r7gd.metal": 2,
  "c7gd.2xlarge": 1,
  "p5.48xlarge": 8,
  "r6idn.large": 1,
  "m6id.metal": 4,
  "x2iedn.4xlarge": 1,
  "h1.16xlarge": 8,
  "r5d.16xlarge": 4,
  "i2.xlarge": 1,
  "r5ad.2xlarge": 1,
  "c6id.32xlarge": 4,
  "m6idn.24xlarge": 4,
  "x2idn.metal": 2,
  "r5d.2xlarge": 1,
  "r7gd.2xlarge": 1,
  "x2gd.12xlarge": 2,
  "m5dn.metal": 4,
  "r5d.8xlarge": 2,
  "c5d.18xlarge": 2,
  "m5ad.xlarge": 1,
  "x2idn.16xlarge": 1,
  "i3.xlarge": 1,
  "m5d.2xlarge": 1,
  "r5d.metal": 4,
  "c5d.metal": 4,
  "r6gd.16xlarge": 2,
  "m6id.4xlarge": 1,
  "z1d.12xlarge": 2,
  "i2.4xlarge": 4,
  "z1d.metal": 2,
  "x2idn.32xlarge": 2,
  "r6idn.32xlarge": 4,
  "c3.4xlarge": 2,
  "c7gd.metal": 2,
  "c3.2xlarge": 2,
  "r6id.metal": 4,
  "c7gd.8xlarge": 1,
  "g5.xlarge": 1,
  "m6idn.metal": 4,
  "z1d.large": 1,
  "m6gd.8xlarge": 1,
  "m5dn.4xlarge": 2,
  "r5ad.xlarge": 1,
  "r6id.8xlarge": 1,
  "g6.16xlarge": 2,
  "i3.16xlarge": 8,
  "r6idn.metal": 4,
  "g6.xlarge": 1,
  "x2gd.large": 1,
  "i3.8xlarge": 4,
  "g6.12xlarge": 4,
  "r5dn.12xlarge": 2,
  "r6id.large": 1,
  "c7gd.12xlarge": 2,
  "m5dn.24xlarge": 4,
  "m3.2xlarge": 2,
  "m5dn.16xlarge": 4,
  "r6gd.8xlarge": 1,
  "c6id.12xlarge": 2,
  "r5dn.16xlarge": 4,
  "z1d.6xlarge": 1,
  "m5d.12xlarge": 2,
  "r5ad.16xlarge": 4,
  "c5d.xlarge": 1,
  "x1e.16xlarge": 1,
  "i2.8xlarge": 8,
  "g6.2xlarge": 1,
  "g4dn.xlarge": 1,
  "x2iedn.16xlarge": 1,
  "is4gen.large": 1,
  "im4gn.4xlarge": 1,
  "i3.large": 1,
  "c6id.metal": 4,
  "im4gn.large": 1,
  "x1.32xlarge": 2,
  "m6idn.8xlarge": 1,
  "x2iedn.24xlarge": 2,
  "m6gd.2xlarge": 1,
  "c6id.xlarge": 1,
  "m5ad.16xlarge": 4,
  "c5ad.8xlarge": 2,
  "c5ad.large": 1,
  "c6gd.4xlarge": 1,
  "x2iedn.32xlarge": 2,
  "i4i.32xlarge": 8,
  "g4ad.16xlarge": 2,
  "r6idn.12xlarge": 2,
  "g5.8xlarge": 1,
  "i3en.xlarge": 1,
  "m6id.24xlarge": 4,
  "i3en.2xlarge": 2,
  "c6gd.2xlarge": 1,
  "dl1.24xlarge": 4,
  "c6id.2xlarge": 1,
  "i3.metal": 8,
  "r7gd.12xlarge": 2,
  "m6id.8xlarge": 1,
  "x1e.xlarge": 1,
  "r5ad.4xlarge": 2,
  "r5dn.4xlarge": 2,
  "gr6.4xlarge": 1,
  "i3.2xlarge": 1,
  "im4gn.16xlarge": 4,
  "r5d.12xlarge": 2,
  "d3.4xlarge": 12,
  "m6idn.16xlarge": 2,
  "c6gd.medium": 1,
  "i4i.xlarge": 1,
  "i4i.12xlarge": 3,
  "i3en.large": 1,
  "x1e.4xlarge": 1,
  "gr6.8xlarge": 2,
  "is4gen.medium": 1,
  "d2.4xlarge": 12,
  "r5dn.2xlarge": 1,
  "m3.large": 1,
  "m3.medium": 1,
  "g6.4xlarge": 1,
  "g4dn.16xlarge": 1,
  "i3en.metal": 8,
  "g5.48xlarge": 2,
  "i3.4xlarge": 2,
  "g4dn.8xlarge": 1,
  "m1.small": 1,
  "m7gd.2xlarge": 1,
  "r6gd.12xlarge": 2,
  "i4i.8xlarge": 2,
  "m6id.large": 1,
  "c6gd.8xlarge": 1,
  "f1.4xlarge": 1,
  "c5d.9xlarge": 1,
  "g4dn.2xlarge": 1,
  "m5d.4xlarge": 2,
  "m1.medium": 1,
  "m1.large": 2,
  "i3en.6xlarge": 2,
  "c6id.4xlarge": 1,
  "z1d.3xlarge": 1,
  "c6gd.12xlarge": 2,
  "f1.16xlarge": 4,
  "m2.xlarge": 1,
  "d2.xlarge": 3,
  "c7gd.4xlarge": 1,
  "g4dn.4xlarge": 1,
  "m6gd.large": 1,
  "is4gen.8xlarge": 4,
  "g4ad.xlarge": 1,
  "d3en.xlarge": 2,
  "p3dn.24xlarge": 2,
  "r5dn.24xlarge": 4,
  "c6gd.large": 1,
  "d3en.12xlarge": 24,
  "x2iedn.8xlarge": 1
}


def expand_ec2_instance_image(old_instances, ec2_region_amis):
    """Filter to set the image for each instance, if not already specified."""
    instances = []

    for old_instance in old_instances:
        instance = copy.deepcopy(old_instance)

        if "image" not in instance:
            instance["image"] = ec2_region_amis[instance["region"]]

        instances.append(instance)

    return instances


def expand_ec2_instance_volumes(old_instances, ec2_ami_properties):
    """
    Expand the instance volume list according to a set of AWS specific transformations.

    Operations performed:
    * format volume to use required format for ec2_instance module
    * translates a device name of 'root' to the given root device name
    * sets delete_on_termination to true if it's not implied by attach_existing or explicitly set to be false.

    """
    instances = []
    EBS_KEYS = [
        "ebs",
        "encrypted",
        "volume_type",
        "volume_size",
        "delete_on_termination",
        "iops",
        "kms_key_id",
    ]

    for old_instance in old_instances:
        ephemeral_count = 0
        instance = copy.deepcopy(old_instance)
        volumes = []
        for vol in instance.get("volumes", []):
            volume = copy.deepcopy(vol)
            _vars = volume.get("vars", {})
            # we want to format our volume to match the new module
            # ec2_instance. We either want an ebs volume or a store volume
            # priorize ebs over ephemeral volume
            if any(ebs_key in volume for ebs_key in EBS_KEYS):
                ebs = volume.get("ebs", {})
                volume_type = volume.pop("volume_type", "gp2")
                ebs["encrypted"] = volume.pop("encrypted", False)
                ebs["volume_type"] = volume_type
                ebs["volume_size"] = volume.pop("volume_size")
                ebs["delete_on_termination"] = volume.pop(
                    "delete_on_termination", not volume.get("attach_existing", False)
                )
                if "iops" in volume and "iops" not in ebs:
                    ebs["iops"] = volume.pop("iops")
                if "kms_key_id" in volume and "kms_key_id" not in ebs:
                    ebs["kms_key_id"] = volume.pop("kms_key_id")
                volume.update({"ebs": ebs})
                # remove ephemeral since this would not be taken into account
                # by module since ebs options are defined.
                if "ephemeral" in volume:
                    volume.pop("ephemeral")
            elif "ephemeral" in volume:
                if instance and instance.get("type") not in EPHEMERAL_STORAGE:
                    raise AnsibleFilterError(
                        f"ephemeral storage unavailable for {instance['type']}")

                max_ephemeral_storage = EPHEMERAL_STORAGE.get(instance["type"])
                ephemeral_count += 1
                if ephemeral_count > max_ephemeral_storage:
                    error_msg = (
                        f"cannot configure more than {max_ephemeral_storage} ephemeral storage "
                        f"for instance {instance['type']}, at least {ephemeral_count} found.")
                    raise AnsibleFilterError(error_msg)

                volume["virtual_name"] = volume.pop("ephemeral")

            if not (volume_type or "virtual_name" in volume):
                raise AnsibleFilterError(
                    f"volume_type/ephemeral not specified for volume {volume['device_name']}"
                )

            if volume["device_name"] == "root":
                volume["device_name"] = ec2_ami_properties[instance["image"]][
                    "root_device_name"
                ]
                if "mountpoint" in _vars or "volume_for" in _vars:
                    raise AnsibleFilterError(
                        "root volume cannot have mountpoint/volume_for set"
                    )
            volumes.append(volume)

        instance["volumes"] = volumes
        instances.append(instance)

    return instances

def _detect_if_ips_are_private_only(aws_item):
    #default is True, meaning we must receive a public IP from amazon
    #unless user decides to not get one
    assign_public_ip = aws_item["item"].get("assign_public_ip", True)
    return assign_public_ip == False

def extract_instance_vars(ec2_jobs_results):
    instances = []
    for node in ec2_jobs_results:
        item = node["item"]
        netiface = node["instances"][0].get("network_interfaces")[0]
        private_ip_only = _detect_if_ips_are_private_only(item)
        public_ip = netiface.get("association", {}).get("public_ip", "")
        instance = {
              "ip_address": netiface.get("private_ip_address") if private_ip_only else public_ip,
              "Name": item['item'].get("Name"),
              "node": item['item'].get("node"),
              "add_to_inventory": not item['item'].get("provision_only"),
              "platform": "aws",
              "public_ip" : public_ip,
              "vars": export_vars(item["item"]),
              }
        instances.append(instance)
    return instances


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
                    volume["ebs"]["volume_size"] != ec2_volume["size"]
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
            "extract_instance_vars": extract_instance_vars,
            "match_existing_volumes": match_existing_volumes,
        }
