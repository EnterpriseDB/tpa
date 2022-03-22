#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import boto3
import sys

from . import CloudPlatform

AWS_DEFAULT_INSTANCE_TYPE = "t3.micro"
AWS_DEFAULT_REGION = "eu-west-1"
AWS_DEFAULT_VOLUME_DEVICE_NAME = "/dev/xvd"


class aws(CloudPlatform):

    def __init__(self, name, arch):
        super().__init__(name, arch)
        self.ec2 = {}
        self.preferred_python_version = "python3"

    def add_platform_options(self, p, g):
        if self.arch.name != "Images":
            g.add_argument("--region", default=AWS_DEFAULT_REGION)
        g.add_argument("--instance-type", default=AWS_DEFAULT_INSTANCE_TYPE, metavar="TYPE")
        g.add_argument("--volume-device-name", default=AWS_DEFAULT_VOLUME_DEVICE_NAME, metavar="DEV")

    def supported_distributions(self):
        return [
            "Debian",
            "Debian-minimal",
            "RedHat",
            "RedHat-minimal",
            "Rocky",
            "Rocky-minimal",
            "Ubuntu",
            "Ubuntu-minimal",
        ]

    def default_distribution(self):
        return "Debian"

    def image(self, label, **kwargs):
        images = {
            "debian": {
                "debian-jessie-amd64-hvm-2017-01-15-1221-ebs": {
                    "versions": ["8", "jessie"],
                    "preferred_python_version": "python2",
                    "owner": "379101102735",
                    "user": "admin",
                },
                "debian-stretch-hvm-x86_64-gp2-2021-12-30-21724": {
                    "versions": ["9", "stretch"],
                    "owner": "379101102735",
                    "user": "admin",
                },
                "debian-10-amd64-20210721-710": {
                    "versions": ["10", "buster", "default"],
                    "owner": "136693071363",
                    "user": "admin",
                },
                "debian-11-amd64-20210814-734": {
                    "versions": ["11", "bullseye"],
                    "owner": "136693071363",
                    "user": "admin",
                },
            },
            "redhat": {
                "RHEL-7.9_HVM-20210208-x86_64-0-Hourly2-GP2": {
                    "versions": ["7"],
                    "preferred_python_version": "python2",
                    "owner": "309956199498",
                    "user": "ec2-user",
                },
                "RHEL-8.4.0_HVM-20210825-x86_64-0-Hourly2-GP2": {
                    "versions": ["8", "default"],
                    "owner": "309956199498",
                    "user": "ec2-user",
                },
            },
            "rocky": {
                "Rocky-8-ec2-8.5-20211114.2.x86_64": {
                    "versions": ["8", "default"],
                    "preferred_python_version": "python3",
                    "owner": "792107900819",
                    "user": "rocky",
                }
            },
            "ubuntu": {
                "ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20210721": {
                    "versions": ["16.04", "xenial"],
                    "owner": "099720109477",
                    "user": "ubuntu",
                },
                "ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-20210907": {
                    "versions": ["18.04", "bionic"],
                    "owner": "099720109477",
                    "user": "ubuntu",
                },
                "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20220131": {
                    "versions": ["20.04", "focal", "default"],
                    "owner": "099720109477",
                    "user": "ubuntu",
                },
            },
        }

        # Transform the table of known images into a form that allows for direct
        # lookup based on label and version.

        amis = {}
        for d in images:
            amis[d] = {}
            for n in images[d]:
                entry = images[d][n]
                for v in entry["versions"]:
                    amis[d][v] = {"name": n, **entry}

        image = {}

        if label in self.supported_distributions():
            label = label.replace("-minimal", "").lower()
            version = kwargs.get("version") or "default"
            image = amis.get(label, {}).get(version)
            if not image:
                print(
                    "ERROR: cannot determine AMI name for %s/%s" % (label, version),
                    file=sys.stderr,
                )
                sys.exit(-1)
            del image["versions"]
            if "preferred_python_version" in image:
                self.preferred_python_version = image["preferred_python_version"]
                del image["preferred_python_version"]
        else:
            image["name"] = label

        if kwargs.get("lookup", False):
            image.update(**self._lookup_ami(image, kwargs["region"]))

        return image

    def _lookup_ami(self, image, region):
        if not region in self.ec2:
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
            raise Exception("Expected 1 match for %s, found %d" % (image["name"], n))
        return {"image_id": r["Images"][0]["ImageId"]}

    def update_cluster_tags(self, cluster_tags, args, **kwargs):
        if args["owner"] is not None:
            cluster_tags["Owner"] = cluster_tags.get("Owner", args["owner"])

    zones_per_region = {
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

    def update_locations(self, locations, args, **kwargs):
        region = args.get("region")
        subnets = args["subnets"]
        for li, location in enumerate(locations):
            location["subnet"] = location.get("subnet", subnets[li])
            region = location.get("region", region)
            if region:
                location["region"] = region
                azs = self.zones_per_region[region]
                az = region + azs[li % len(azs)]
                location["az"] = location.get("az", az)

    def update_cluster_vars(self, cluster_vars, args, **kwargs):
        cluster_vars["preferred_python_version"] = cluster_vars.get(
            "preferred_python_version", self.preferred_python_version
        )

    def update_instance_defaults(self, instance_defaults, args, **kwargs):
        y = self.arch.load_yaml("platforms/aws/instance_defaults.yml.j2", args)
        if y:
            instance_defaults.update(y)

    def update_instances(self, instances, args, **kwargs):
        for instance in instances:

            self.update_barman_instance_volume(self.arch, args, instance)

    def process_arguments(self, args):
        s = args.get("platform_settings") or {}

        ec2_vpc = {"Name": "Test", "cidr": str(self.arch.net)}
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
