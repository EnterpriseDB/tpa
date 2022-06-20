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
        Update instances with bdr-always-on specific changes.
        Invoke BDR generic update to process updates common to multiple BDR
        architectures (BDR-A-ON, BDR-autoscale).
        """

        super().update_instances(instances)
        self._update_instances_harp_etcd(instances)

    def _update_instances_harp_etcd(self, instances):
        """
        When using 'harp_consensus_protocol: etcd', explicitly add 'etcd' to the
        role for each of the following instances:
        - BDR Primary ('bdr' role)
        - BDR Logical Standby ('bdr' + 'readonly' roles)
        - only for the Bronze layout: BDR Witness ('bdr' + 'witness' roles)
        - only for the Gold layout: Barman ('barman' role)
        Note that this is one of the possible choices for the template, and not
        necessarily the best one; different placements are possible, as long as
        there are three etcd instances for each location, and the BDR nodes have
        a local etcd node, which seems convenient.
        Args:
            instances (list): list of instances to update
        """
        if self.args.get("harp_consensus_protocol") == "etcd":
            for instance in instances:
                if self._instance_roles(instance).isdisjoint(
                    self._etcd_harp_exclude_roles
                ) and "bdr" in self._instance_roles(instance):
                    instance["role"].append("etcd")
                if self.args["layout"] == "gold" and "barman" in self._instance_roles(
                    instance
                ):
                    instance["role"].append("etcd")

    @property
    def _etcd_harp_exclude_roles(self):
        """
        Instance roles that should not run etcd while using harp consensus etcd.
        Returns: Set of role names
        """
        _exclude_roles = {
            "replica",
            "subscriber-only",
            "witness",
        }
        if self.args["layout"] == "bronze":
            _exclude_roles.difference_update({"witness"})
        return _exclude_roles
