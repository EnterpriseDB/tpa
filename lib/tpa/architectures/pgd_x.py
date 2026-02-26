#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

from tpa.exceptions import PGDXArchitectureError
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
            ("14", "6"),
            ("15", "6"),
            ("16", "6"),
            ("17", "6"),
            ("18", "6"),
        ]

    def num_instances(self):
        """
        Should do a calculation here - temporarily, we just return a
        big enough number
        """
        return 16

    def default_edb_repos(self, cluster_vars) -> List[str]:
        """PGD-X requires the postgres_distributed repository.

        This is added to whatever repositories have already been determined
        by the parent class ('standard' or 'enterprise', depending on flavour
        or in principle on other requested software)
        """
        return super().default_edb_repos(cluster_vars) + ['postgres_distributed']

    def default_location_names(self):
        return ["first"]

    def validate_arguments(self, args, platform):
        super().validate_arguments(args, platform)
        self._validate_camo(args)
        if not self.args["location_names"]:
            self.args["location_names"] = self.default_location_names()
    
    
    def _validate_camo(self, args):
        camo = args.get("enable_camo", False)
        data_nodes = args.get("data_nodes_per_location")
        if camo:
            if self.args.get("postgres_flavour") not in ["edbpge", "epas"]:
                raise PGDXArchitectureError(
                    "You must use Postgres Extended or EPAS to --enable-camo"
                )
            if data_nodes != 2:
                raise PGDXArchitectureError(
                    "Cannot enable CAMO with --data-nodes-per-location " \
                    "different than 2 data nodes"
                )

    def _update_instance_camo(self, cluster):
        """
        If --enable-camo is specified, we collect all the instances with role
        [bdr,primary] and no partner already set and set them pairwise to be
        each other's CAMO partners.

        For each location, identifies BDR data nodes without existing CAMO
        partners and pairs them. CAMO requires exactly 2 data nodes per location;
        raises an error if this constraint is not met.

        Requires postgres_flavour to be edbpge or epas.
        """
        cluster.set_var("bdr_commit_scopes", [])
        subgroups = []
        scope = "camo"

        # Here we set all the BDR Primary nodes found per location, group them by pairs and then 
        # define their own CAMO "bdr_commit_scope"
        for location in cluster.locations:
            bdr_primaries = cluster.instances.in_location(location.name).with_bdr_node_kind("data").select(lambda i: "bdr_node_camo_partner" not in i.host_vars)
            if len(bdr_primaries) != 2:
                continue
            a, b = bdr_primaries[0], bdr_primaries[1]
            a.set_hostvar("bdr_node_camo_partner", b.name)
            b.set_hostvar("bdr_node_camo_partner", a.name)

            subgroup = self._sub_group_name(location.name)
            subgroups.append(subgroup)

            cluster.group.group_vars["bdr_commit_scopes"].append(
                {
                    "name": scope,
                    "origin": subgroup,
                    "rule": f"ALL ({subgroup}) ON durable CAMO DEGRADE ON (timeout = 60s, require_write_lead = true) TO ASYNC",
                }
            )
        
        # Set the "default_commit_scope" option to "camo" inside "bdr_node_groups"
        for node_group in cluster.group.group_vars["bdr_commit_scopes"]:
            if node_group["name"] in subgroups:
                node_group.setdefault("options", {})
                node_group["options"]["default_commit_scope"] = scope

    def update_cluster_vars(self, cluster_vars):
        super().update_cluster_vars(cluster_vars)

        cluster_vars.update({"pgd_flavour": "expanded"})

        top_group = cluster_vars["bdr_node_group"]

        # Get or create the bdr_node_groups list
        existing_groups = cluster_vars.setdefault("bdr_node_groups", [])

        # Find the top-level group if it already exists (from parent class)
        top_group_entry = None
        for group in existing_groups:
            if group["name"] == top_group:
                top_group_entry = group
                break

        # If top-level group doesn't exist, create it
        if top_group_entry is None:
            top_group_entry = {"name": top_group}
            existing_groups.append(top_group_entry)

        # Merge routing options into the top-level group
        routing_enabled = self.args["pgd_routing"] == "global"
        if "options" not in top_group_entry:
            top_group_entry["options"] = {}
        top_group_entry["options"]["enable_routing"] = routing_enabled

        # Add location subgroups
        location_names = self.args["location_names"]
        for _location in location_names:
            new_group = {
                "name": self._sub_group_name(_location),
                "parent_group_name": top_group,
                "options": {
                    "location": _location,
                    "enable_routing": not routing_enabled,  # Opposite of parent
                },
            }
            existing_groups.append(new_group)

    def update_instances(self, cluster):
        instances = cluster.instances
        self._update_instance_camo(cluster)
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
            "--enable-camo",
            action="store_true",
            dest="enable_camo",
            help="Enable Commit At Most Once (CAMO) on the data nodes",
        )
