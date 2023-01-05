#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

from .bdr import BDR
from ..exceptions import ArchitectureError
from typing import List, Tuple
import re


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
            "--add-witness-node-per-location",
            action="store_true",
            help="should there be witness node in every location",
            dest="witness_node_per_location",
        )
        g.add_argument(
            "--add-witness-only-location",
            dest="witness_only_location",
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
        witness_only_location = self.args["witness_only_location"]
        data_nodes_per_location = self.args["data_nodes_per_location"]
        witness_node_per_location = self.args["witness_node_per_location"]

        if data_nodes_per_location < 2:
            errors.append("--data-nodes-per-location cannot be less than 2")

        if data_nodes_per_location * len(location_names) > 1000:
            errors.append(
                "PGD does not support more than 1000 nodes per cluster, please modify --data-nodes-per-location value"
            )

        # We must add a witness automatically if there are only two data
        # nodes per location. Otherwise, we allow adding a witness only
        # if the number of data nodes is even.

        if data_nodes_per_location == 2:
            self.args["witness_node_per_location"] = True

        if witness_node_per_location and data_nodes_per_location % 2 != 0:
            errors.append(
                "--add-witness-node-per-location can only be specified with even number of data nodes per location"
            )

        if witness_only_location and len(location_names) % 2 == 0:
            errors.append(
                "--add-witness-only-location can only be specified with odd number of locations"
            )

        if witness_only_location and witness_only_location not in location_names:
            errors.append(
                "--add-witness-only-location '%s' must be included in location list"
                % self.args["witness_only_location"]
            )

        if self.args["active_locations"]:
            for aloc in self.args["active_locations"]:
                if aloc not in self.args["location_names"]:
                    errors.append(
                        "--active-locations '%s' must be included in location list"
                        % aloc
                    )
        if errors:
            raise ArchitectureError(*(f"PGD-Always-ON parameter {e}" for e in errors))

    def update_cluster_vars(self, cluster_vars):
        """
        Define bdr_node_groups, along with any pgd-proxy options required,
        under cluster_vars.
        """
        super().update_cluster_vars(cluster_vars)

        top = self.args["bdr_node_group"]
        bdr_node_groups = [{"name": top}]

        for loc in self.args.get("location_names"):
            group = {
                "name": self._sub_group_name(loc),
                "parent_group_name": top,
                "options": {"location": loc},
            }

            # Disable subgroup raft and proxy routing for witness-only
            # locations, and enable proxy routing for locations with a proxy
            # (subgroup raft will be enabled based on enable_subgroup_raft").
            if self._is_witness_only_location(loc):
                group["options"].update(
                    {
                        "enable_raft": False,
                    }
                )
            else:
                group["options"].update(
                    {
                        "enable_proxy_routing": True,
                    }
                )

            bdr_node_groups.append(group)

        cluster_vars.update(
            {
                "bdr_node_groups": bdr_node_groups,
                "enable_subgroup_raft": "false",
                "default_pgd_proxy_options": {
                    "listen_port": 6432,
                },
            }
        )

    def update_instances(self, instances):
        """
        Update instances with bdr node and proxy configuration specific
        to PGD-Always-ON.
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

        for instance in instances:
            role = self._instance_roles(instance)
            instance_vars = instance.get("vars", {})
            location = instance["location"]

            # Make sure at least one instance in each location has "backup"
            # set to the Barman instance in the same location.
            if "bdr" in role and "witness" not in role:
                b = barman_instances_by_location.get(location)
                if b:
                    instance["backup"] = b["Name"]
                    del barman_instances_by_location[location]

            # All BDR instances need bdr_child_group set; nodes that pgd-proxy
            # can route to also need routing options set.
            if "bdr" in role:
                instance_vars.update(
                    {"bdr_child_group": self._sub_group_name(location)}
                )

                if (
                    "subscriber-only" not in role
                    and "readonly" not in role
                    and "witness" not in role
                ):
                    instance_vars.update(
                        {
                            "bdr_node_options": {
                                "route_priority": 100,
                            }
                        }
                    )

            # Proxy nodes may need some proxy-specific configuration.
            if "pgd-proxy" in role:
                instance_vars.update(
                    {"bdr_child_group": self._sub_group_name(location)}
                )
                fallback_groups = [
                    self._sub_group_name(l) for l in self._fallback_locations(location)
                ]
                if fallback_groups:
                    instance_vars.update(
                        {
                            "pgd_proxy_options": {
                                "fallback_groups": fallback_groups,
                            }
                        }
                    )

            if instance_vars:
                instance["vars"] = instance_vars

    def _sub_group_name(self, loc):
        """
        Returns a name for the BDR subgroup in the given location.
        """
        loc = re.sub("[^a-z0-9_]", "_", loc)
        return f"{loc}_subgroup"

    def _is_witness_only_location(self, location):
        """
        Returns true if the given location is a witness-only location,
        and false otherwise.
        """
        return location == self.args.get("witness_only_location")

    def _fallback_locations(self, location):
        """
        Returns a list of fallback location names for the pgd-proxy in the given
        location to use.

        BDR currently supports only one fallback location, so we return a list
        containing only one location for now (cf. bdr_alter_proxy_option_sql).
        The basis of selection is only that it must be a different location
        which is not a witness-only location.

        Args:
            location: the location for which to return fallback locations

        Returns:
            list: list of fallback location names, may be empty if no fallback
            locations are available
        """

        possible_fallback_locations = [
            l
            for l in self.args.get("location_names")
            if not (l == location or self._is_witness_only_location(l))
        ]

        # The correct use of fallback locations depends on the number of
        # locations available (e.g., one has to be careful to avoid cyclic
        # dependencies), requires the user to be aware of the implications, and
        # may need user input as well. Since it can't be handled with an on/off
        # switch for now, we disable it altogether by pretending that there are
        # no fallback locations available.
        possible_fallback_locations = []

        return sorted(possible_fallback_locations)[:1]
