#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.
import argparse

from ..architecture import Architecture
from ..exceptions import ArchitectureError


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

        assert isinstance(p, argparse.ArgumentParser)
        fail_over_group = p.add_argument_group(
            "M1 architecture fail-over manager options"
        )
        fail_over_me_group = fail_over_group.add_mutually_exclusive_group()

        fail_over_me_group.add_argument(
            "--failover-manager",
            choices=["efm", "patroni", "repmgr"],
            help="The type of fail-over manager to use for the cluster.",
        )

        fail_over_me_group.add_argument(
            "--enable-efm",
            action="store_const",
            const="efm",
            dest="failover_manager",
            help="Enable EDB Failover Manager",
        )

        fail_over_me_group.add_argument(
            "--enable-repmgr",
            action="store_const",
            const="repmgr",
            dest="failover_manager",
            help="Enable Replication Manager as HA fail-over manager",
        )

        fail_over_me_group.add_argument(
            "--enable-patroni",
            action="store_const",
            const="patroni",
            dest="failover_manager",
            help="Enable Patroni HA cluster fail-over manager",
        )

        g.add_argument(
            "--enable-haproxy",
            action="store_true",
            help="Enable HAproxy layer hosts when using Patroni fail-over manager",
        )
        g.add_argument(
            "--patroni-dcs",
            choices=["etcd"],
            required=False,
            default="etcd",
            help="The Distributed Configuration Store to use with Patroni",
        )

    def validate_arguments(self, args):
        super().validate_arguments(args)

        if args.get("enable_haproxy") and args.get("failover_manager") != "patroni":
            raise ArchitectureError(
                "HAproxy can only be enabled when used in conjunction with Patroni."
            )

        if (
            (args.get("distribution") == "RedHat" and args.get("os_version") == "7")
            or args.get("os_image") == "tpa/centos:7"
        ) and (
            args.get("failover_manager") == "patroni" and args.get("enable_haproxy")
        ):
            raise ArchitectureError(
                "TPA does not support Patroni with HAproxy on RedHat/CentOS 7"
            )
        if args.get("failover_manager") == "repmgr" and args.get("postgres_flavour") == "epas":
            raise ArchitectureError(
                f"TPA does not support repmgr with {args.get('postgres_flavour')}"
            )

    def num_instances(self):
        return (
            3
            + self.args.get("cascaded_replicas", 1)
            + (
                3 if self.args.get("failover_manager") == "patroni" else 0
            )  # DCS nodes (etcd)
            + (2 if self.args.get("enable_haproxy") else 0)
        )

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
            not tpa_2q_repositories
            or "products/default/release" not in given_repositories
        ):
            tpa_2q_repositories.append("products/default/release")

        if tpa_2q_repositories:
            cluster_vars.update(
                {
                    "tpa_2q_repositories": tpa_2q_repositories,
                }
            )

        cluster_vars.update(
            {
                "failover_manager": failover_manager,
            }
        )

        if failover_manager == "patroni":
            # Ensure nodes are members of a single etcd_location per cluster for patroni.
            cluster_vars["etcd_location"] = "main"

            if postgres_flavour == "pgextended":
                raise ArchitectureError(
                    "2Q Postgres Extended is not compatible with the failover manager Patroni."
                    " Try `--postgres-flavour edbpge` instead."
                )

            edb_repositories = set(cluster_vars.get("edb_repositories") or [])

            # Adds repo containing postgres as a dependency, as use of any edb v2 repo disables v1/2q repos
            # When generic support for M1 with EDB v2 repos is supported this can be removed
            edb_repositories.add(
                "enterprise" if postgres_flavour == "epas" else "standard"
            )

            # Add EDB v2 package repos to include Patroni packages
            edb_repositories.add("community_360")
            cluster_vars["edb_repositories"] = list(edb_repositories)
