#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

import boto3

from . import CloudPlatform
from ..exceptions import AWSPlatformError

AWS_DEFAULT_INSTANCE_TYPE = "t3.micro"
AWS_DEFAULT_REGION = "eu-west-1"
AWS_DEFAULT_VOLUME_DEVICE_NAME = "/dev/xvd"
AWS_ZONES_PER_REGION = {
    "ap-northeast-1": ["a", "b", "c", "d"],
    "ap-northeast-2": ["a", "b", "c", "d"],
    "ap-northeast-3": ["a", "b", "c"],
    "ap-south-1": ["a", "b", "c"],
    "ap-southeast-1": ["a", "b", "c"],
    "ap-southeast-2": ["a", "b", "c"],
    "ca-central-1": ["a", "b", "d"],  # !!!
    "eu-central-1": ["a", "b", "c"],
    "eu-north-1": ["a", "b", "c"],
    "eu-west-1": ["a", "b", "c"],
    "eu-west-2": ["a", "b", "c"],
    "eu-west-3": ["a", "b", "c"],
    "sa-east-1": ["a", "b", "c"],
    "us-east-1": ["a", "b", "c", "d", "e", "f"],
    "us-east-2": ["a", "b", "c"],
    "us-west-1": ["a", "b", "c"],
    "us-west-2": ["a", "b", "c", "d"],
}


class aws(CloudPlatform):
    def __init__(self, name, arch):
        super().__init__(name, arch)
        self.ec2 = {}
        self.preferred_python_version = "python3"

    @property
    def zones_per_region(self):
        return AWS_ZONES_PER_REGION

    @property
    def default_volume_device_group(self):
        return AWS_DEFAULT_VOLUME_DEVICE_NAME

    def add_platform_options(self, p, g):
        if self.arch.name != "Images":
            region_group = g.add_mutually_exclusive_group()
            region_group.add_argument(
                "--region",
                default=AWS_DEFAULT_REGION,
                choices=self.zones_per_region.keys(),
            )
            region_group.add_argument(
                "--regions",
                choices=self.zones_per_region.keys(),
                nargs="+",
            )
        g.add_argument(
            "--instance-type", default=AWS_DEFAULT_INSTANCE_TYPE, metavar="TYPE"
        )
        g.add_argument("--cluster-bucket")

    def supported_distributions(self):
        return [
            "Debian",
            "Debian-arm",
            "Debian-minimal",
            "RedHat",
            "RedHat-arm",
            "RedHat-minimal",
            "Rocky",
            "Rocky-minimal",
            "Ubuntu",
            "Ubuntu-minimal",
            "SLES",
        ]

    def default_distribution(self):
        return "Debian"

    def image(self, label, **kwargs):
        images = {
            "debian": {
                "debian-10-amd64-20240204-1647": {
                    "versions": ["10", "buster"],
                    "owner": "136693071363",
                    "user": "admin",
                },
                "debian-11-amd64-20240104-1616": {
                    "versions": ["11", "bullseye", "default"],
                    "owner": "136693071363",
                    "user": "admin",
                },
                "debian-12-amd64-20240201-1644": {
                    "versions": ["12", "bookworm"],
                    "owner": "136693071363",
                    "user": "admin",
                },
            },
            "debian-arm": {
                "debian-12-arm64-20231013-1532": {
                    "versions": ["12", "bookworm", "default"],
                    "owner": "136693071363",
                    "user": "admin",
                },
            },
            "redhat": {
                "RHEL-7.9_HVM-20221027-x86_64-0-Hourly2-GP2": {
                    "versions": ["7"],
                    "preferred_python_version": "python2",
                    "owner": "309956199498",
                    "user": "ec2-user",
                },
                "RHEL-8.7.0_HVM-20230330-x86_64-56-Hourly2-GP2": {
                    "versions": ["8", "default"],
                    "owner": "309956199498",
                    "user": "ec2-user",
                },
                "RHEL-9.0.0_HVM-20240227-x86_64-39-Hourly2-GP3": {
                    "versions": ["9"],
                    "owner": "309956199498",
                    "user": "ec2-user",
                },
            },
            "redhat-arm": {
                "RHEL-9.4.0_HVM-20240605-arm64-82-Hourly2-GP3": {
                    "versions": ["9", "default"],
                    "owner": "309956199498",
                    "user": "ec2-user",
                },
            },
            "rocky": {
                "Rocky-8-EC2-Base-8.9-20231119.0.x86_64": {
                    "versions": ["8", "default"],
                    "preferred_python_version": "python3",
                    "owner": "792107900819",
                    "user": "rocky",
                    "os_family": "RedHat",
                }
            },
            "ubuntu": {
                "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20240228": {
                    "versions": ["20.04", "focal"],
                    "owner": "099720109477",
                    "user": "ubuntu",
                },
                "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-20240301": {
                    "versions": [
                        "22.04",
                        "jammy",
                    ],
                    "owner": "099720109477",
                    "user": "ubuntu",
                },
                "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20240801": {
                    "versions": [
                        "24.04",
                        "noble",
                        "default",
                    ],
                    "owner": "099720109477",
                    "user": "ubuntu",
                },
            },
            "sles": {
                "suse-sles-15-sp6-v20250130-hvm-ssd-x86_64": {
                    "versions": ["15"],
                    "preferred_python_version": "python3",
                    "owner": "013907871322",
                    "user": "ec2-user",
                }
            },
        }

        image = {}

        if label in self.supported_distributions():
            label_base = label.replace("-minimal", "")
            version = kwargs.get("version") or "default"
            # Find the name and other attributes of any entry under
            # images that matches the desired label and version.
            try:
                image = next(
                    {"name": k, **v}
                    for k, v in images[label_base.lower()].items()
                    if version in v["versions"]
                )
            except (KeyError, StopIteration):
                raise AWSPlatformError(
                    f"ERROR: cannot determine AMI name for {label_base}/{version}"
                )

            image["os"] = label_base
            image["os_family"] = image.get("os_family", label_base)
            try:
                if "default" in image["versions"]:
                    image["versions"].remove("default")
                image["version"] = image["versions"][0]
            except IndexError:
                pass
            del image["versions"]

        else:
            image["name"] = label

        if kwargs.get("lookup", False):
            image.update(**self._lookup_ami(image, kwargs["region"]))

        if (
            self._is_default_ec2_instance_type()
            and self._is_rhel_image(image["os"])
            and not self._is_an_arm64_image(image["os"])
        ):
            self.arch.args["instance_type"] = "t3.medium"

        if self._is_default_ec2_instance_type() and self._is_an_arm64_image(
            image["os"]
        ):
            self.arch.args["instance_type"] = "t4g.medium"

        return image

    def _is_rhel_image(self, image):
        accepted_rhel_images = ("rhel", "redhat", "rocky")
        return image.lower().startswith(accepted_rhel_images)

    def _is_an_arm64_image(self, image):
        accepted_arm64_images = ("debian-arm", "redhat-arm")
        return image.lower().startswith(accepted_arm64_images)

    def _is_default_ec2_instance_type(self):
        return self.arch.args.get("instance_type") == AWS_DEFAULT_INSTANCE_TYPE

    def _lookup_ami(self, image, region):
        if region not in self.ec2:
            self.ec2[region] = boto3.client("ec2", region_name=region)
        filters = [
            {"Name": "name", "Values": [image["name"]]},
        ]
        if "owner" in image:
            filters.append(
                {
                    "Name": "owner-id",
                    "Values": [image["owner"]],
                }
            )
        v = self.arch.args["verbosity"]
        if v > 0:
            print('aws: Looking up AMI "%s" in "%s"' % (image["name"], region))
        r = self.ec2[region].describe_images(Filters=filters)
        if v > 1:
            print("aws: Got lookup result: %s" % str(r))
        n = len(r["Images"])
        if n != 1:
            raise AWSPlatformError(
                "Expected 1 match for %s, found %d" % (image["name"], n)
            )
        return {"image_id": r["Images"][0]["ImageId"]}

    def update_cluster_tags(self, cluster_tags, args, **kwargs):
        if args["owner"] is not None:
            cluster_tags["Owner"] = cluster_tags.get("Owner", args["owner"])

    def update_locations(self, locations, args, **kwargs):
        regions = args.get("regions")
        subnets = args["subnets"]
        for li, location in enumerate(locations):
            location["subnet"] = location.get("subnet", subnets[li])
            region = regions[li % len(regions)]
            if region:
                location["region"] = region
                azs = self.zones_per_region[region]
                az = region + azs[(li // len(regions)) % len(azs)]
                location["az"] = location.get("az", az)

    def update_cluster_vars(self, cluster_vars, args, **kwargs):
        pass

    def update_instance_defaults(self, instance_defaults, args, **kwargs):
        y = self.arch.load_yaml("platforms/aws/instance_defaults.yml.j2", args)
        if y:
            instance_defaults.update(y)

    def update_instances(self, instances, args, **kwargs):
        for instance in instances:
            self.update_barman_instance_volume(self.arch, args, instance)

    def validate_arguments(self, args):
        """
        Validate aws specific arguments
        """

        # ensure regions given are not duplicated.
        if args["regions"]:
            args["regions"] = list(dict.fromkeys(args["regions"]))
            if len(args["regions"]) > 1:
                print(
                    """Warning:
When using multiple regions you MUST manually edit config.yml to ensure that
`ec2_vpc` `cidr` don't overlap to allow vpc peering between regions.
`cluster_rules` and `locations` `subnet` values must all be changed
accordingly. See documentation https://documentation.enterprisedb.com/tpa/release/latest/platform-aws/#regions

VPC peering must be setup manually after `tpaexec provision` is run.
                    """
                )
        else:
            args["regions"] = [args.get("region")]

    def process_arguments(self, args):
        s = args.get("platform_settings") or {}
        ec2_vpc = {}
        for region in args["regions"]:
            ec2_vpc[region] = {"Name": "Test", "cidr": str(self.arch.net)}

        ec2_vpc.update(args.get("ec2_vpc", {}))
        s["ec2_vpc"] = ec2_vpc

        if args["image"]:
            ec2_ami = {"Name": args["image"]["name"]}
            if "owner" in args["image"]:
                ec2_ami["Owner"] = args["image"]["owner"]
            ec2_ami.update(args.get("ec2_ami", {}))
            s["ec2_ami"] = ec2_ami

        self.set_cluster_rules(args, settings=s)

        cluster_bucket = args.get("cluster_bucket")
        if cluster_bucket:
            s["cluster_bucket"] = cluster_bucket

        s["ec2_instance_reachability"] = "public"

        args["platform_settings"] = s
