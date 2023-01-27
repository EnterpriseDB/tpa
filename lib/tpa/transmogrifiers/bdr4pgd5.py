#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

from ..exceptions import ConfigureError
from ..transmogrifier import Transmogrifier, opt
from ..changedescription import ChangeDescription
from ..checkresult import CheckResult
from .repositories import Repositories


class BDR4PGD5(Transmogrifier):
    def __init__(self):
        self.require(Repositories(default_repos=["postgres_distributed"]))

    @classmethod
    def options(cls):
        return {
            **opt(
                "--architecture",
                choices=["PGD-Always-ON"],
                dest="target_architecture",
                help="change the cluster's architecture",
            ),
            **opt(
                "--pgd-proxy-routing",
                help="Configure each PGD-Proxy to route connections to a \
                globally-elected write leader (global)\
                or a write leader within its own location (local)",
                choices=["global", "local"],
                dest="pgd_proxy_routing",
                default=None,
                required=True,
            ),
        }

    def is_applicable(self, cluster):
        return self.args.target_architecture == "PGD-Always-ON"

    def check(self, cluster):
        res = CheckResult()

        source_arch = cluster.architecture
        if source_arch == "PGD-Always-ON":
            res.error("This is already a PGD-Always-ON cluster")
        elif source_arch != "BDR-Always-ON":
            res.error(
                f"Don't know how to convert architecture {source_arch} to PGD-Always-ON"
            )

        bdr_locations = [
            l
            for l in cluster.locations
            if len(cluster.instances.in_location(l.name).with_role("bdr")) > 0
        ]

        for loc in bdr_locations:
            bdr_instances = len(
                cluster.instances.in_location(loc.name).with_role("bdr")
            )

            if bdr_instances <= 2:
                res.warning(
                    f"Location '{loc.name}' has 2 or less data nodes. "
                    "You might want to consider adding node(s) to this location."
                )
            if bdr_instances % 2 == 0:
                res.warning(
                    f"Location '{loc.name}' has an even number of data nodes. "
                    "This is not an optimal configuration for the consensus protocol."
                )

        if len(cluster.instances) > 1000:
            res.error("PGD-Always-ON does not support more than 1000 nodes per cluster")

        if len(bdr_locations) == 2:
            res.error(
                "PGD-Always-ON clusters with only two locations will "
                "lose global consensus entirely if any one location fails. "
                "Consider adding another location (which may be a --witness-only-location)."
            )

        return res

    def apply(self, cluster):
        bdr_version = cluster.vars.get("bdr_version")
        if bdr_version and int(bdr_version) != 4:
            raise ConfigureError(
                f"Don't know how to convert bdr_version from {bdr_version} to 5"
            )
        else:
            cluster.vars["bdr_version"] = "5"

        cluster._architecture = self.args.target_architecture

        cluster.vars["failover_manager"] = "pgd"

        # Change postgres_flavour from pgextended to edbpge.

        if cluster.vars.get("postgres_flavour") == "pgextended":
            cluster.vars["postgres_flavour"] = "edbpge"

        instances = cluster.instances

        if instances.with_role("harp-proxy").add_role("pgd-proxy"):
            cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}

        # Initialise bdr_node_groups (which is not expected to be set in a BDR4
        # cluster—it was supported in theory, but in practice it wouldn't have
        # worked properly).
        #
        # We create one additional BDR group per location.

        top = cluster.vars["bdr_node_group"]
        bdr_node_groups = [{"name": top}]

        pgd_proxy_routing = self.args.pgd_proxy_routing
        if pgd_proxy_routing == "global":
            bdr_node_groups[0]["options"] = {"enable_proxy_routing": True}

        for loc in cluster.locations:

            loc_instances = instances.in_location(loc.name)

            if len(loc_instances.with_role("bdr")) > 0:
                group = {
                    "name": loc.sub_group_name,
                    "parent_group_name": top,
                    "options": {"location": loc.name},
                }

            # Local routing enables subgroup RAFT and proxy routing,
            # and witness-only locations have both disabled.

                loc_witnesses = loc_instances.with_role("witness")

                for instance in loc_instances:
                    if instance in instances.with_role("bdr") + instances.with_role(
                        "pgd-proxy"
                    ):
                        instance.host_vars["bdr_child_group"] = group["name"]

                    # Add route_priority to bdr data nodes that pgd-proxy
                    # nodes can route to.
                    if instance in instances.with_role("bdr").without_roles(
                        ["witness", "subscriber-only", "readonly"]
                    ):
                        instance.host_vars["bdr_node_options"] = {
                            "route_priority": 100,
                        }

                if set(loc_witnesses.get_names()) == set(loc_instances.get_names()):
                    loc._witness_only = True
                if loc.witness_only:
                    group["options"].update(
                        {
                            "enable_raft": False,
                            "enable_proxy_routing": False,
                        }
                    )

                elif pgd_proxy_routing == "local":
                    group["options"].update(
                        {
                            "enable_raft": True,
                            "enable_proxy_routing": True,
                        }
                    )
                bdr_node_groups.append(group)

        cluster.vars.update({"bdr_node_groups": bdr_node_groups})

        if "harp_http_options" in cluster.vars:
            cluster.vars["pgd_http_options"] = cluster.vars["harp_http_options"].copy()

        # To configure CAMO, we need to define one commit scope per subgroup
        # containing CAMO pairs, and set it as the default commit scope for the
        # corresponding subgroup. (Note that it's possible, albeit unlikely, for
        # a BDR4 cluster to have bdr_commit_scopes defined.)

        bdr_commit_scopes = cluster.vars.get("bdr_commit_scopes", [])

        camo_instances = instances.with_hostvar("bdr_node_camo_partner")
        for instance in camo_instances:
            partner_name = instance.host_vars.get("bdr_node_camo_partner")
            partner = camo_instances.with_name(partner_name).maybe()
            if not partner:
                raise ConfigureError(
                    f"Can't find CAMO partner named {partner_name} for "
                    "instance {instance.name}"
                )

            # To enable CAMO, the partners must be in the same subgroup, and the
            # group must comprise 2 data nodes, or 2 data nodes and 1 witness.
            # Nothing else will work.

            subgroup = instance.host_vars.get("bdr_child_group")
            partner_group = partner.host_vars.get("bdr_child_group")
            if subgroup != partner_group:
                raise ConfigureError(
                    f"Instances {instance.name} (group: {subgroup}) and "
                    "{partner_name} (group: {partner_group}) must be in the "
                    "same node group to enable CAMO"
                )

            members = instances.with_role("bdr").with_hostvar(
                "bdr_child_group", value=subgroup
            )

            data_nodes = members.with_bdr_node_kind("data")
            witness_nodes = members.with_bdr_node_kind("witness")

            if (
                len(data_nodes) != 2
                or len(witness_nodes) not in [0, 1]
                or len(members) > len(data_nodes) + len(witness_nodes)
            ):
                raise ConfigureError(
                    f"Cannot enable CAMO for subgroup {subgroup}. Group must "
                    "contain exactly 2 data nodes + 1 optional witness only."
                )

            scope = {
                "name": "camo",
                "origin": subgroup,
                "rule": f"ALL ({subgroup}) ON durable CAMO DEGRADE ON (timeout = 3600s) TO ASYNC",
            }

            # Do nothing if the first partner already defined the scope.
            if [
                s
                for s in bdr_commit_scopes
                if s["name"] == scope["name"] and s["origin"] == scope["origin"]
            ]:
                continue

            bdr_commit_scopes.append(scope)

        if bdr_commit_scopes:
            cluster.vars["bdr_commit_scopes"] = bdr_commit_scopes

    def description(self, cluster):
        items = [
            "Change bdr_version",
            "Define bdr_node_groups",
            "Change harp-proxy instances to pgd-proxy",
            "Change failover_manager to pgd",
            "Define proxy routing local or global",
        ]

        if cluster.instances.with_hostvar("bdr_node_camo_partner"):
            items.append("Define a commit scope to enable CAMO")

        return ChangeDescription(
            title="Convert BDR-Always-ON to PGD-Always-ON",
            items=items,
        )
