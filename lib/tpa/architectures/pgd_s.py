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
        Should do a calculation here - temporarily, we just return a
        big enough number
        """
        return 8

    def default_location_names(self):
        return ["first"]

    def upper_limit_of_data_nodes(self):
        """
        Returns the upper limit of data nodes that can be added to the cluster.
        """
        return 4

    def validate_arguments(self, args, platform):
        super().validate_arguments(args, platform)

        if not self.args["location_names"]:
            self.args["location_names"] = self.default_location_names()

        num_locations = len(self.args["location_names"])
        data_nodes_per_location = self.args["data_nodes_per_location"]
        upper_limit = self.upper_limit_of_data_nodes()
        _total_datanodes_in_cluster =  num_locations * data_nodes_per_location

        if _total_datanodes_in_cluster > upper_limit:
            raise PGDArchitectureError(
                f"PGD-S is limited up to {upper_limit} data nodes in total across all locations"
            )

    def update_cluster_vars(self, cluster_vars):
        super().update_cluster_vars(cluster_vars)

        cluster_vars.update(
            {
                "pgd_flavour": "essential"
            }
        )

    def add_architecture_options(self, p, g):
        def data_nodes_validator(value):
            try:
                value = int(value)
            except ValueError:
                raise PGDArchitectureError(
                    f"Invalid value for --data-nodes-per-location: {value}"
                )
            if value < 1:
                raise PGDArchitectureError(
                    f"Invalid value for --data-nodes-per-location: {value}"
                )
            return value

        super().add_architecture_options(p, g)
        g.add_argument(
            "--data-nodes-per-location",
            type=data_nodes_validator,
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
