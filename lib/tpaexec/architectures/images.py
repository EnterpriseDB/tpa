#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from ..architecture import Architecture

import re

from ..exceptions import ImagesArchitectureError


class Images(Architecture):
    def add_architecture_options(self, p, g):
        g.add_argument(
            "--image-name",
            metavar="NAME",
        )
        g.add_argument(
            "--image-label",
            metavar="LABEL",
            default="Postgres",
        )
        g.add_argument(
            "--image-version",
            metavar="VER",
            default="10",
        )
        g.add_argument(
            "--distributions",
            metavar="LABEL",
            nargs="+",
        )
        if self.platform.name != "docker":
            g.add_argument(
                "--regions",
                metavar="REGION",
                nargs="+",
            )

    def supported_platforms(self):
        return ["aws", "docker"]

    def update_argument_defaults(self, defaults):
        defaults.update({"distribution": None})

        if self.platform.name == "aws":
            defaults.update(
                {
                    "image_name": "TPA-{distribution}-{label}-{version}-{date}",
                    "distributions": ["Debian", "RedHat", "Ubuntu"],
                    "regions": [
                        "eu-west-1",
                        "eu-west-2",
                        "eu-west-3",
                        "eu-central-1",
                        "us-east-1",
                        "us-east-2",
                        "us-west-1",
                        "us-west-2",
                    ],
                }
            )
        elif self.platform.name == "docker":
            defaults.update(
                {
                    "image_name": "tpa/{distribution}-{label}:{version}-{date}",
                    "distributions": ["RedHat"],
                    "regions": ["irrelevant"],
                }
            )

    # We don't need to generate random hostnames
    def hostnames(self, num):
        return []

    # We don't have anything to set in self.args['image']
    def image(self):
        return {}

    # We don't use main.yml.j2 either
    def load_topology(self, args):
        instances = []

        regions = args["regions"]
        distributions = args["distributions"]
        if args.get("distribution"):
            raise ImagesArchitectureError(
                "Please use --distributions (not --distribution) for this architecture"
            )

        for i, r in enumerate(regions):
            for j, d in enumerate(distributions):
                image = self.platform.image(d, lookup=True, region=r)
                instance = {
                    "node": i * len(distributions) + j + 1,
                    "Name": ("%s-%s" % (re.sub("[^a-zA-Z0-9-]", "-", d), r)).lower(),
                    "image": image.get("image_id", image["name"]),
                    "location": i,
                }
                if "user" in image:
                    instance["vars"] = {"ansible_user": image["user"]}
                instances.append(instance)

        args.update({"instances": instances})

    def update_locations(self, locations):
        for i, r in enumerate(self.args["regions"]):
            locations[i]["region"] = r

    def update_cluster_vars(self, cluster_vars):
        cluster_vars.update(
            {
                "image_name": self.args["image_name"],
                "image_label": self.args["image_label"],
                "image_version": self.args["image_version"],
            }
        )

    def num_instances(self):
        return len(self.args["regions"]) * len(self.args["distributions"])

    def num_locations(self):
        return len(self.args["regions"])

    def default_location_names(self):
        return [chr(ord("a") + i) for i in range(self.num_locations())]
