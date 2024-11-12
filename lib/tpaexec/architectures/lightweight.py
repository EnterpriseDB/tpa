#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

from .bdr import BDR
from ..exceptions import ArchitectureError
from typing import List, Tuple, Union
import re
from argparse import SUPPRESS
from packaging.version import Version, InvalidVersion, parse


class Lightweight(BDR):
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
                "postgres_volume_size": 64,
                "failover_manager": "pgd",
                "proxy_nodes_per_location": 0,
            }
        )

    def default_location_names(self):
        return ["primary", "dr"]

    def num_data_locations(self):

        return 2

    def num_instances(self):
        res = 3
        # Up to N proxies per data location
        num_proxies = self.args.get("proxy_nodes_per_location") or 0
        res += num_proxies

        return res

    def validate_arguments(self, args):
        super().validate_arguments(args)

        errors = []
        if not self.args["location_names"]:
            self.args["location_names"] = self.default_location_names()

        location_names = self.args["location_names"]

        if len(location_names) != 2:
            errors.append("--location-names must contain 2 locations")

        if errors:
            raise ArchitectureError(*(f"Lightweight parameter {e}" for e in errors))

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

        bdr_node_groups[0]["options"] = {"enable_proxy_routing": True}

        location_names = self.args["location_names"]

        for loc in location_names:
            group = {
                "name": self._sub_group_name(loc),
                "parent_group_name": top,
                "options": {"location": loc},
            }

            bdr_node_groups.append(group)

        cluster_vars.update(
            {
                "bdr_node_groups": bdr_node_groups,
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

            # All BDR instances need bdr_child_group set; nodes that pgd-proxy
            # can route to also need routing options set.
            if "bdr" in role:
                instance_vars.update(
                    {"bdr_child_group": self._sub_group_name(location)}
                )

                instance_vars.update(
                    {
                        "bdr_node_options": {
                            "route_priority": (
                                100
                                if instance["location"]
                                == self.args["location_names"][0]
                                else 90
                            ),
                        }
                    }
                )
                if instance["location"] == self.args["location_names"][1]:
                    instance_vars["bdr_node_options"].update(
                        {
                            "route_fence": True,
                        }
                    )

            # Proxy nodes may need some proxy-specific configuration.
            if "pgd-proxy" in role:
                instance_vars.update(
                    {"bdr_child_group": self._sub_group_name(location)}
                )

            if instance_vars:
                instance["vars"] = instance_vars

        # Generate the commit_scope for lightweight architecture
        # in the main location.
        cluster_vars = self.args["cluster_vars"]
        cluster_vars.setdefault("bdr_commit_scopes", [])

        group = cluster_vars["bdr_node_groups"][1]["name"]
        scope = "lightweight_scope"

        commit_scopes = [
            (s["name"], s["origin"])
            for s in cluster_vars["bdr_commit_scopes"]
        ]
        if (scope, group) not in commit_scopes:
            cluster_vars["bdr_commit_scopes"].append(
                {
                    "name": scope,
                    "origin": group,
                    "rule": "ALL ORIGIN_GROUP SYNCHRONOUS_COMMIT DEGRADE ON (timeout = 20s, require_write_lead = true) TO ASYNC",
                }
            )

        # Apply the commit_scope to the main location subgroup
        for g in cluster_vars["bdr_node_groups"]:
            if g["name"] == group:
                g.setdefault("options", {})
                g["options"]["default_commit_scope"] = scope


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
