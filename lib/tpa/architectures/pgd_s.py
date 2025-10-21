#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

from ..architecture import Architecture
from ..exceptions import PGDArchitectureError
from .pgd import PGD
from typing import List, Tuple

from argparse import SUPPRESS


class PGDS(PGD):
    pass

    @property
    def name(self):
        """
        The name of this architecture as it goes in config.yml
        """
        return "PGD-S"

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
        Both layouts need 4 instances, plus any subscriber-only nodes,
        plus a pem server if requested.
        """
        return 4 + self.args["subscriber_only_nodes"] + ("enable_pem" in self.args)

    def default_edb_repos(self, cluster_vars) -> List[str]:
        """PGD-S needs enterprise repo since essentials packages live there.
        any occurence of standard repo would be redondant with enterprise,
        that's why standard is discarded (removed only if exists).

        Args:
            cluster_vars (dict): cluster vars for the cluster being created

        Returns:
            List[str]: List of repositories required for the PGD-S architecture
        """
        base_repos = set(super().default_edb_repos(cluster_vars))
        base_repos.discard("standard")
        # eventually, PGD-S will be available in the "enterprise" repo, but for
        # now we also need postgres_distributed
        return list(base_repos.union(["enterprise", "postgres_distributed"]))

    def validate_arguments(self, args, platform):
        super().validate_arguments(args, platform)

        """
        The layout has been determined either directly or by falling back to
        the default of "standard". If the user has supplied location names
        then we check they have supplied the right number; if they haven't,
        then we fill in the right number of placeholder names.
        """
        layouts = {
            'standard': [ 'first' ],
            'near-far': [ 'first', 'second' ],
        }
        default_locations = layouts[args['layout']]

        if self.args['location_names']:
            if len(self.args['location_names']) != len(default_locations):
                 raise PGDArchitectureError(
                     f"{args['layout']} requires exactly {len(default_locations)} locations"
                 )
        else:
            self.args["location_names"] = default_locations


    def update_cluster_vars(self, cluster_vars):
        super().update_cluster_vars(cluster_vars)

        cluster_vars.update(
            {
                "pgd_flavour": "essential"
            }
        )

    def add_architecture_options(self, p, g):
        super().add_architecture_options(p, g)

        g.add_argument(
            "--layout",
            dest="layout",
            choices=["standard", "near-far"],
            default="standard",
            help="standard (1-location) or near-far (2-location) layout",
        )
        g.add_argument(
            "--add-subscriber-only-nodes",
            type=int,
            choices=range(0, 11),
            default=0,
            dest="subscriber_only_nodes",
            help="number of subscriber-only nodes (maximum 10)",
        )

    def load_standard(self, args, cluster):
        # 3 data nodes, 1 barman
        for node in range(1, 4):
            cluster.add_instance(
                instance_name = args["hostnames"][node],
                location_name = args["location_names"][0],
                roles = ['bdr'],
                settings = {
                    "node": node,
                }
            )


    def load_near_far(self, args, cluster):
        for node in range(1, 3):
            cluster.add_instance(
                instance_name = args["hostnames"][node],
                location_name = args["location_names"][0],
                roles = ['bdr'],
                settings = {
                    "node": node,
                }
            )
        cluster.add_instance(
            instance_name = args["hostnames"][3],
            location_name = args["location_names"][1],
            roles = ['bdr'],
            settings = {
                "node": 3,
            }
        )

    def load_topology(self, args, cluster):
        if args["layout"] == "standard":
            self.load_standard(args, cluster)

        if args["layout"] == "near-far":
            self.load_near_far(args, cluster)

        # barman and subscriber-only nodes are the same for either layout
        cluster.add_instance(
            instance_name = args["hostnames"][4],
            location_name = args["location_names"][0],
            roles = ['barman'],
            settings = {
                "node": 4,
            }
        )
        for n in range(5, 5 + args["subscriber_only_nodes"]):
            cluster.add_instance(
                instance_name = args["hostnames"][n],
                location_name = args["location_names"][0],
                roles = ['bdr', 'subscriber_only'],
                settings = {
                    "node": n,
                }
            )
