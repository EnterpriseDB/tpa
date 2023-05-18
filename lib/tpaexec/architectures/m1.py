#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

from ..architecture import Architecture


class M1(Architecture):
    def add_architecture_options(self, p, g):
        g.add_argument(
            "--num-cascaded-replicas",
            type=int,
            metavar="N",
            help="number of replicas cascaded from first replica",
            dest="cascaded_replicas",
            default=1,
        )

    def num_instances(self):
        return 3 + self.args.get("cascaded_replicas", 1)

    def default_location_names(self):
        return ["main", "dr"]

    def update_instances(self, instances):

        # If --enable-pem is specified, we collect all the instances with role
        # [primary, replica, witness] and append 'pem-agent' role to the existing
        # set of roles assigned to them. We later add a dedicated 'pemserver'
        # instance to host our PEM server.

        if self.args.get("enable_pem"):
            for instance in instances:
                ins_defs = self.args["instance_defaults"]
                role = instance.get("role", ins_defs.get("role", []))
                if "primary" in role or "replica" in role or "witness" in role:
                    instance["role"].append("pem-agent")
                if "barman" in role and self.args.get("enable_pg_backup_api", False):
                    instance["role"].append("pem-agent")
            n = instances[-1].get("node")
            instances.append(
                {
                    "node": n + 1,
                    "Name": "pemserver",
                    "role": ["pem-server"],
                    "location": self.args["locations"][0]["Name"],
                }
            )
    def update_cluster_vars(self, cluster_vars):
        """
        Makes architecture-specific changes to cluster_vars if required
        """
        tpa_2q_repositories = self.args.get("tpa_2q_repositories") or []
        postgres_flavour = self.args.get("postgres_flavour")
        failover_manager = self.args.get("failover_manager")

        given_repositories = " ".join(tpa_2q_repositories)

        if postgres_flavour == "epas" and (
            not tpa_2q_repositories or
            "products/default/release" not in given_repositories):
            tpa_2q_repositories.append("products/default/release")

        if tpa_2q_repositories:
            cluster_vars.update(
                {
                    "tpa_2q_repositories": tpa_2q_repositories,
                }
            )

        if not failover_manager:
            if postgres_flavour == "epas":
                failover_manager = "efm"
            elif postgres_flavour in ["pgextended", "edbpge", "postgresql"]:
                failover_manager = "repmgr"

        if failover_manager:
            cluster_vars.update(
                {
                    "failover_manager": failover_manager,
                }
            )
