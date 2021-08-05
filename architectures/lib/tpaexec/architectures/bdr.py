#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

from ..architecture import Architecture


class BDR(Architecture):
    def add_architecture_options(self, p, g):
        g.add_argument(
            "--bdr-node-group",
            metavar="NAME",
            help="name of BDR node group",
            default="bdrgroup",
        )
        g.add_argument(
            "--bdr-database",
            metavar="NAME",
            help="name of BDR-enabled database",
            default="bdrdb",
        )
        g.add_argument(
            "--enable-camo",
            action="store_true",
            help="assign instances pairwise as CAMO partners",
        )

    def cluster_vars_args(self):
        return super().cluster_vars_args() + ["bdr_node_group", "bdr_database"]

    def update_cluster_vars(self, cluster_vars):
        cluster_vars.update(
            {
                "repmgr_failover": "manual",
                "postgres_coredump_filter": "0xff",
            }
        )

    def update_instances(self, instances):

        # If --enable-camo is specified, we collect all the instances with role
        # [bdr,primary] and no partner already set and set them pairwise to be
        # each other's CAMO partners. This is crude, but it's good enough to
        # experiment with CAMO on a two- or four-node BDR-Simple cluster.

        if self.args.get("enable_camo", False):
            bdr_primaries = []
            id = self.args["instance_defaults"]
            for i in instances:
                vars = i.get("vars", {})
                role = i.get("role", id.get("role", []))
                if "bdr" in role and "primary" in role and "readonly" not in role:
                    if not "bdr_node_camo_partner" in vars:
                        bdr_primaries.append(i)

            idx = 0
            while idx + 1 < len(bdr_primaries):
                a = bdr_primaries[idx]
                b = bdr_primaries[idx + 1]

                a_vars = a.get("vars", {})
                a_vars["bdr_node_camo_partner"] = b.get("Name")
                a["vars"] = a_vars

                b_vars = b.get("vars", {})
                b_vars["bdr_node_camo_partner"] = a.get("Name")
                b["vars"] = b_vars

                idx += 2
