#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

from .bdr import BDR
from ..exceptions import ArchitectureError
from typing import List, Tuple, Union
import re
from argparse import SUPPRESS
from packaging.version import Version, InvalidVersion, parse


class PGD_Always_ON(BDR):
    def supported_versions(self) -> List[Tuple[str, str]]:
        return [
            ("12", "5"),
            ("13", "5"),
            ("14", "5"),
            ("15", "5"),
            ("16", "5"),
            ("17", "5"),
        ]

    def add_architecture_options(self, p, g):
        super().add_architecture_options(p, g)
        g.add_argument(
            "--pgd-proxy-routing",
            help="configure each PGD-Proxy to route connections to a globally-elected write leader (global) or a write leader within its own location (local)",
            choices=["global", "local"],
            dest="pgd_proxy_routing",
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

    def update_argument_defaults(self, defaults):
        super().update_argument_defaults(defaults)
        defaults.update(
            {
                "barman_volume_size": 128,
                "postgres_volume_size": 64,
                "failover_manager": "pgd",
                "proxy_nodes_per_location": 0,
            }
        )

    def default_location_names(self):
        return ["first"]

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

        # Up to N proxies per data location
        num_proxies = self.args.get("proxy_nodes_per_location") or 0
        res += self.num_data_locations() * num_proxies

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
        self.args["pgd_proxy_routing"]

        if data_nodes_per_location < 2:
            errors.append("--data-nodes-per-location cannot be less than 2")

        if data_nodes_per_location * len(location_names) > 1000:
            raise ArchitectureError(
                "PGD-Always-ON does not support more than 1000 nodes per cluster"
            )

        if len(location_names) == 2:
            print(
                "WARNING: PGD-Always-ON clusters with only two locations will "
                "lose global consensus entirely if any one location fails.\n"
                "Consider adding another location (which may be a --witness-only-location)"
            )

        if data_nodes_per_location % 2 == 0:
            self.args["witness_node_per_location"] = True

        if witness_node_per_location and data_nodes_per_location % 2 != 0:
            errors.append(
                "--add-witness-node-per-location can only be specified with even number of data nodes per location"
            )

        if witness_only_location and witness_only_location not in location_names:
            errors.append(
                "--witness-only-location '%s' must be included in location list"
                % witness_only_location
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

        # If --pgd-proxy-routing is set to global, we need to enable
        # proxy routing on the top-level group and all proxies are
        # part of the top-level group. If routing is set to local,
        # we need to enable proxy routing (and enable_raft) on the
        # subgroups we create for each location, and proxies are
        # part of the local subgroup.

        pgd_proxy_routing = self.args["pgd_proxy_routing"]
        if pgd_proxy_routing == "global":
            bdr_node_groups[0]["options"] = {
                "enable_proxy_routing": True,
                "enable_raft": True,
            }
        else:
            bdr_node_groups[0]["options"] = {
                "enable_proxy_routing": False,
                "enable_raft": True,
            }

        location_names = self.args["location_names"]
        for loc in location_names:
            group = {
                "name": self._sub_group_name(loc),
                "parent_group_name": top,
                "options": {"location": loc, "enable_raft": False},
            }

            # Local routing enables subgroup RAFT and proxy routing,
            # and witness-only locations have both disabled.
            if self._is_witness_only_location(loc):
                group["options"].update({"enable_raft": False})

            elif pgd_proxy_routing == "local":
                group["options"].update(
                    {
                        "enable_raft": True,
                        "enable_proxy_routing": True,
                    }
                )

            bdr_node_groups.append(group)

        cluster_vars.setdefault("bdr_node_groups", []).extend(bdr_node_groups)
        cluster_vars.update(
            {
                "default_pgd_proxy_options": {
                    "listen_port": self.args["listen_port"],
                },
            }
        )

        bdr_package_version = cluster_vars.get("bdr_package_version")
        sanitized_version, includes_wildcard = self._sanitize_version(
            version_string=bdr_package_version
        )
        if self._is_above_minimum(
            sanitized_version, Version("5.5"), includes_wildcard=includes_wildcard
        ):
            cluster_vars.update(
                {
                    "default_pgd_proxy_options": {
                        "listen_port": self.args["listen_port"],
                        "read_listen_port": self.args["read_listen_port"],
                    }
                }
            )
        self._update_pgd_probes(cluster_vars)

    def default_edb_repos(self, cluster_vars) -> List[str]:
        return super().default_edb_repos(cluster_vars) + ["postgres_distributed"]

    def _update_pgd_probes(self, cluster_vars):
        http = {}
        if "enable_pgd_probes" in self.args:
            http = {"pgd_http_options": {"enable": True}}
            if self.args["enable_pgd_probes"] in ["https"]:
                http["pgd_http_options"].update({"secure": True})
        cluster_vars.update(http)

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

        # Map BDR group names to a list of instances in the group.
        bdr_primaries_by_group = {}
        for i in instances:
            if self._is_bdr_primary(i):
                group = self._instance_bdr_group(i)
                bdr_primaries_by_group.setdefault(group, [])
                bdr_primaries_by_group[group].append(i)

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

                # CAMO partners need special handling in BDRv5. We must create
                # a commit scope for the group, and ensure that the group does
                # not have more than two data nodes.

                if "bdr_node_camo_partner" in instance_vars:
                    cluster_vars = self.args["cluster_vars"]
                    cluster_vars.setdefault("bdr_commit_scopes", [])

                    group = instance_vars["bdr_child_group"]
                    scope = "camo"

                    # Whichever is the first instance in the CAMO pair can
                    # create the new commit scope.
                    commit_scopes = [
                        (s["name"], s["origin"])
                        for s in cluster_vars["bdr_commit_scopes"]
                    ]
                    if (scope, group) not in commit_scopes:
                        cluster_vars["bdr_commit_scopes"].append(
                            {
                                "name": scope,
                                "origin": group,
                                "rule": f"ALL ({group}) ON durable CAMO DEGRADE ON (timeout = 60s,  require_write_lead = true) TO ASYNC",
                            }
                        )

                    if len(bdr_primaries_by_group[group]) > 2:
                        raise ArchitectureError(
                            f"Cannot enable CAMO for node group {group} with >2 data nodes"
                        )

                    for g in cluster_vars["bdr_node_groups"]:
                        if g["name"] == group:
                            g.setdefault("options", {})
                            g["options"]["default_commit_scope"] = scope

            # Proxy nodes may need some proxy-specific configuration.
            if "pgd-proxy" in role:
                instance_vars.update(
                    {"bdr_child_group": self._sub_group_name(location)}
                )

            if instance_vars:
                instance["vars"] = instance_vars

    def _instance_bdr_group(self, instance):
        """Returns the name of the node group that this instance is (or rather,
        will be) a member of."""
        v = instance.get("vars", {})
        return v.get("bdr_child_group", self._sub_group_name(instance.get("location")))

    def _sub_group_name(self, loc):
        """
        Returns a name for the BDR subgroup in the given location.
        """
        loc = re.sub("[^a-z0-9_]", "_", loc.lower())
        return f"{loc}_subgroup"

    def _is_witness_only_location(self, location):
        """
        Returns true if the given location is a witness-only location,
        and false otherwise.
        """
        return location == self.args.get("witness_only_location")

    def _sanitize_version(
        self, version_string
    ) -> Union[Tuple[Version, bool], Tuple[None, bool]]:
        try:
            version_parts = version_string.split(":", maxsplit=1)[-1].split(".")
            if version_parts[1] == "*":
                return parse(version_parts[0]), True
            else:
                return parse(f"{version_parts[0]}.{version_parts[1]}"), False
        except (InvalidVersion, AttributeError) as e:
            return None, False

    def _is_above_minimum(
        self, x: Union[Version, None], y: Version, includes_wildcard: bool
    ) -> bool:
        if x is None:
            return True
        elif includes_wildcard:
            return x.major >= y.major
        else:
            return x >= y
