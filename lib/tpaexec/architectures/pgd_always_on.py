#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from .bdr import BDR
from ..exceptions import ArchitectureError
from typing import List, Tuple


class PGD_Always_ON(BDR):
    def supported_versions(self) -> List[Tuple[str, str]]:
        return [
            ("12", "5"),
            ("13", "5"),
            ("12", "5"),
            ("13", "5"),
            ("14", "5"),
        ]

    def add_architecture_options(self, p, g):
        super().add_architecture_options(p, g)

        g.add_argument(
            "--active-locations",
            help="list of active (write) locations",
            dest="active_locations",
            nargs="+",
        )
        g.add_argument(
            "--data-nodes-per-location",
            type=int,
            dest="data_nodes_per_location",
            default=3,
            help="how many PGD nodes per location should be deployed",
        )
        g.add_argument(
            "--witness-node-per-location",
            action="store_true",
            help="should there be witness node in every location",
            dest="witness_node_per_location",
        )
        g.add_argument(
            "--witness-only-location",
            help="optional witness only location",
            default=None,
        )
        g.add_argument(
            "--cohost-proxies",
            action="store_true",
            help="cohost proxies on PGD data nodes",
            dest="cohost_proxies",
        )

    def update_argument_defaults(self, defaults):
        super().update_argument_defaults(defaults)
        defaults.update(
            {
                "barman_volume_size": 128,
                "postgres_volume_size": 64,
                "failover_manager": "pgd",
            }
        )

    def num_data_locations(self):
        res = len(self.args["location_names"])
        if self.args["witness_only_location"] is not None:
            res -= 1

        return res

    def num_instances(self):
        res = 0

        # PGD data nodes
        res += self.num_data_locations() * self.args["data_nodes_per_location"]

        # Witness nodes per location
        if self.args["witness_node_per_location"]:
            res += self.num_data_locations()

        # 2 Proxies per data location
        if not self.args["cohost_proxies"]:
            res += self.num_data_locations() * 2

        # Barman per data location
        res += self.num_data_locations()

        # Witness only location
        if self.args["witness_only_location"] is not None:
            res += 1

        return res

    def validate_arguments(self, args):
        super().validate_arguments(args)

        errors = []

        if not self.args["location_names"]:
            self.args["location_names"] = self.default_location_names()

        location_names = self.args["location_names"]
        data_nodes_per_location = self.args["data_nodes_per_location"]
        witness_only_location = self.args["witness_only_location"]

        if data_nodes_per_location < 2:
            errors.append("--data-nodes-per-location cannot be less than 2")

        if data_nodes_per_location * len(location_names) > 1000:
            errors.append(
                "PGD does not support more than 1000 nodes per cluster, please modify --data-nodes-per-location value"
            )

        if self.args["witness_node_per_location"] and data_nodes_per_location % 2 != 0:
            errors.append(
                "--witness-node-per-location can only be specified with even number of data nodes per location"
            )

        if witness_only_location and len(location_names) % 2 == 0:
            errors.append(
                "--witness-only-location can only be specified with odd number of locations"
            )

        if witness_only_location and witness_only_location not in location_names:
            errors.append(
                '--witness-only-location location "%s" must be included in location list'
                % self.args["witness_only_location"]
            )

        if self.args["active_locations"]:
            for aloc in self.args["active_locations"]:
                if aloc not in self.args["location_names"]:
                    errors.append(
                        '--active-locations location "%s" must be included in location list'
                        % aloc
                    )
        if errors:
            raise ArchitectureError(*(f"PGD-Always-ON parameter {e}" for e in errors))

    def update_cluster_vars(self, cluster_vars):
        super().update_cluster_vars(cluster_vars)

        top = self.args["bdr_node_group"]
        bdr_node_groups = [{"name": top}]
        for i in range(len(self.args.get("location_names"))):
            bdr_node_groups.append(
                {
                    "name": self._sub_group_name(self.args.get("location_names")[i]),
                    "parent_group_name": top,
                }
            )

        cluster_vars.update(
            {
                "bdr_node_groups": bdr_node_groups,
            }
        )

    def _sub_group_name(self, loc):
        return "s_group_%s" % loc

    def _bdr_primaries(self):
        primaries = []
        for i in self.args["instances"]:
            r = self._instance_roles(i)
            if "bdr" in r and "readonly" not in r and "subscriber-only" not in r:
                primaries.append(i.get("node"))

        return primaries

    def update_instances(self, instances):
        """
        Update instances with bdr-always-on specific changes.
        Invoke BDR generic update to process updates common to multiple BDR
        architectures (BDR-A-ON, BDR-autoscale).
        """

        super().update_instances(instances)

        # Map location names to the corresponding barman instances.
        barman_instances_by_location = dict(
            [
                (x["location"], x)
                for x in instances
                if "barman" in self._instance_roles(x)
            ]
        )

        bdr_primaries = self._bdr_primaries()

        for instance in instances:
            role = self._instance_roles(instance)
            location = instance["location"]

            # Make sure at least one instance in each location has "backup"
            # set to the Barman instance in the same location.
            if "bdr" in role and "witness" not in role:
                b = barman_instances_by_location.get(location)
                if b:
                    instance["backup"] = b["Name"]
                    del barman_instances_by_location[location]

            if instance.get("node") in bdr_primaries:
                vars = instance.get("vars", {})
                vars.update(
                    {
                        "bdr_child_group": self._sub_group_name(location),
                    }
                )
                instance["vars"] = vars
