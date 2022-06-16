#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from .bdr import BDR
from typing import List, Tuple


class BDR_Always_ON(BDR):
    def supported_versions(self) -> List[Tuple[str, str]]:
        return [
            ("11", "3"),
            ("12", "3"),
            ("13", "3"),
            ("12", "4"),
            ("13", "4"),
            ("14", "4"),
        ]

    def add_architecture_options(self, p, g):
        super().add_architecture_options(p, g)
        g.add_argument(
            "--harp-consensus-protocol",
            choices=["etcd", "bdr"],
            required=True,
            help="the consensus protocol to use for HARP v2",
        )

    def update_argument_defaults(self, defaults):
        super().update_argument_defaults(defaults)
        defaults.update(
            {
                "barman_volume_size": 128,
                "postgres_volume_size": 64,
                "failover_manager": "harp",
            }
        )

    def default_layout_name(self):
        return None

    def num_instances(self):
        # This method must be able to return correct results before the layout
        # templates are loaded, so we hardcode the number of instances defined
        # in the various layouts.
        instances_per_layout = {
            "platinum": 13,
            "gold": 11,
            "silver": 6,
            "bronze": 6,
        }
        return instances_per_layout[self.args["layout"]]

    def default_location_names(self):
        return [chr(ord("a") + i) for i in range(self.num_locations())]

    def update_instances(self, instances):
        """
        When using `harp_consensus_protocol: etcd`, explicitly add 'etcd' to the
        role for each BDR primary or witness instance that should run etcd.
        """

        super().update_instances(instances)

        if self.args.get("harp_consensus_protocol") == "etcd":
            ins_defs = self.args["instance_defaults"]
            for i in instances:
                role = i.get("role", ins_defs.get("role", []))
                if (
                    "bdr" in role
                    and "replica" not in role
                    and "readonly" not in role
                    and "subscriber-only" not in role
                ):
                    i["role"].append("etcd")
