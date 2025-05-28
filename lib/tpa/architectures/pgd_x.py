#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

from ..architecture import Architecture
from .pgd import PGD
from typing import List, Tuple

from argparse import SUPPRESS


class PGDX(PGD):

    @property
    def name(self):
        """
        The name of this architecture as it goes in config.yml
        """
        return "PGD-X"

    def supported_versions(self) -> List[Tuple[str, str]]:
        return [
            ("13", "6"),
            ("14", "6"),
            ("15", "6"),
            ("16", "6"),
            ("17", "6"),
        ]

    def num_instances(self):
        """
        Should do a calculation here - temporarily, we just return a
        big enough number
        """
        return 16

    def default_edb_repos(self, cluster_vars) -> List[str]:
        """PGD-X requires postgres_distributed repos contrary to PGD-S
        that only relies on enterprise repo.

        """
        return super().default_edb_repos(cluster_vars) + ['postgres_distributed']

    def default_location_names(self):
        return ["first"]

    def validate_arguments(self, args, platform):
        super().validate_arguments(args, platform)

        if not self.args["location_names"]:
            self.args["location_names"] = self.default_location_names()

    def update_cluster_vars(self, cluster_vars):
        super().update_cluster_vars(cluster_vars)

        cluster_vars.update({"pgd_flavour": "expanded"})

        top_group = cluster_vars["bdr_node_group"]
        bdr_node_groups = [{"name": top_group}]
        if self.args["pgd_routing"] == "global":

            bdr_node_groups[0].update(
                {
                    "options": {
                        "enable_routing": True,
                    }
                }
            )
        else:
            bdr_node_groups[0].update(
                {
                    "options": {
                        "enable_routing": False,
                    }
                }
            )
        location_names = self.args["location_names"]
        for _location in location_names:
            new_group = {
                "name": self._sub_group_name(_location),
                "parent_group_name": top_group,
                "options": {"location": _location},
            }
            if self.args["pgd_routing"] == "global":
                new_group.update(
                    {
                        "options": {
                            "enable_routing": False,
                        }
                    }
                )
            else:
                new_group.update(
                    {
                        "options": {
                            "enable_routing": True,
                        }
                    }
                )

            bdr_node_groups.append(new_group)
        cluster_vars.update({"bdr_node_groups": bdr_node_groups})

    def update_instances(self, cluster):
        instances = cluster.instances
        super().update_instances(cluster)

        for instance in instances:
            instance_vars = instance.host_vars
            location = instance.location
            if "bdr" in self._instance_roles(instance):
                instance_vars.update(
                    {"bdr_child_group": self._sub_group_name(location.name)}
                )

    def add_architecture_options(self, p, g):
        super().add_architecture_options(p, g)
        g.add_argument(
            "--pgd-routing",
            help="configure Connection Manager to route connections to a globally-elected write leader (global) or a write leader within its own location (local)",
            choices=["global", "local"],
            dest="pgd_routing",
            default=None,
            required=True,
        )
        g.add_argument(
            "--data-nodes-per-location",
            type=int,
            dest="data_nodes_per_location",
            default=3,
            help="number of PGD data nodes per location",
        )
        g.add_argument(
            "--add-witness-node-per-location",
            action="store_true",
            help="not needed; witness nodes are added automatically when required",
            dest="witness_node_per_location",
        )
        g.add_argument(
            "--witness-only-location",
            "--add-witness-only-location",
            dest="witness_only_location",
            help="designate a location as a witness-only location (no data nodes)",
            default=None,
        )

        g.add_argument(
            "--cohost-proxies",
            action="store_const",
            const=0,
            dest="proxy_nodes_per_location",
            help="not needed; pgd-proxy runs on the data nodes by default",
        )
        g.add_argument(
            "--add-proxy-nodes-per-location",
            type=int,
            dest="proxy_nodes_per_location",
            help="number of separate PGD-Proxy nodes to add in each location",
        )
        g.add_argument(
            "--enable-pgd-probes",
            choices=["http", "https"],
            nargs="?",
            default=SUPPRESS,
            help="Enable http(s) api endpoints for pgd-proxy such as `health/is-ready` to allow probing proxy's health",
        )
        g.add_argument(
            "--proxy-listen-port",
            type=int,
            dest="listen_port",
            default=6432,
            help="port on which proxy nodes will route traffic to the write leader",
        )
        g.add_argument(
            "--proxy-read-only-port",
            type=int,
            dest="read_listen_port",
            default=6433,
            help="port on which proxy nodes will route read-only traffic to shadow nodes",
        )
