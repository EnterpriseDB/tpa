#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

import argparse

from typing import List

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
        failover_group = p.add_argument_group(
            "M1 architecture failover manager options"
        )
        failover_me_group = failover_group.add_mutually_exclusive_group(required=True)

        failover_me_group.add_argument(
            "--failover-manager",
            choices=["efm", "patroni", "repmgr"],
            help="The type of failover manager to use for the cluster.",
        )

        failover_me_group.add_argument(
            "--enable-efm",
            action="store_const",
            const="efm",
            dest="failover_manager",
            help="Enable EDB Failover Manager",
        )

        failover_me_group.add_argument(
            "--enable-repmgr",
            action="store_const",
            const="repmgr",
            dest="failover_manager",
            help="Enable Replication Manager as HA failover manager",
        )

        failover_me_group.add_argument(
            "--enable-patroni",
            action="store_const",
            const="patroni",
            dest="failover_manager",
            help="Enable Patroni HA cluster failover manager",
        )

        g.add_argument(
            "--enable-haproxy",
            action="store_true",
            help="Enable HAproxy layer hosts when using Patroni failover manager",
        )
        g.add_argument(
            "--patroni-dcs",
            choices=["etcd"],
            required=False,
            default="etcd",
            help="The Distributed Configuration Store to use with Patroni",
        )

        layout_group = p.add_argument_group("M1 architecture layout options")
        layout_group.add_argument(
            "--data-nodes-per-location",
            type=int,
            metavar="N",
            help="Number of data nodes in each location",
            default=2,
        )
        layout_group.add_argument(
            "--witness-only-location",
            help="A location with a witness node only",
        )
        layout_group.add_argument(
            "--single-node-location",
            help="A location with a single database node",
        )
        layout_group.add_argument(
            "--primary-location",
            help="The location for the primary database node",
        )

    def active_locations(self):
        locations = self.all_locations()
        if self.args.get("single_node_location"):
            locations.pop()
        if self.args.get("witness_only_location"):
            locations.pop()
        return locations

    def all_locations(self):
        if self.args.get("location_names"):
            return self.args.get("location_names").copy()
        else:
            return self.default_location_names()

    def validate_arguments(self, args):
        super().validate_arguments(args)

        # locations:
        # for the template, we need to end up with the primary location
        # first in the active locations list
        locations = self.all_locations()

        if args.get("single_node_location"):
            if args["single_node_location"] not in locations:
                raise ArchitectureError(
                    f"Location {args['single_node_location']} unknown"
                )
            locations.remove(args["single_node_location"])

        if args.get("witness_only_location"):
            if args["witness_only_location"] not in locations:
                raise ArchitectureError(
                    f"Location {args['witness_only_location']} unknown"
                )
            if args.get("failover_manager") not in ["repmgr", "efm"]:
                raise ArchitectureError(
                    "Witness-only locations are supported only with repmgr or efm"
                )
            if len(locations) < 3:
                raise ArchitectureError(
                    "Witness-only locations require at least two active locations"
                )
            locations.remove(args["witness_only_location"])

        if args.get("primary_location"):
            if args["primary_location"] not in locations:
                raise ArchitectureError(
                    f"Location {args.get['primary_location']} unknown"
                )
            if args["primary_location"] != locations[0]:
                locations.remove(args["primary_location"])
                locations.insert(0, args["primary_location"])

        else:
            args["primary_location"] = locations[0]

        args["active_locations"] = locations

        # failover manager compatibility checks
        if args.get("enable_haproxy") and args.get("failover_manager") != "patroni":
            raise ArchitectureError(
                "HAproxy can only be enabled when used in conjunction with Patroni."
            )

        if (
            args.get("failover_manager") == "patroni"
            and args.get("enable_haproxy")
            and (
                (args.get("distribution") == "RedHat" and args.get("os_version") == "7")
                or args.get("os_image") == "tpa/centos:7"
            )
        ):
            raise ArchitectureError(
                "TPA does not support Patroni with HAproxy on RedHat/CentOS 7"
            )

        if (
            args.get("failover_manager") == "patroni"
            and len(self.active_locations()) > 1
        ):
            raise ArchitectureError(
                "TPA does not support Patroni with multiple locations"
            )
        if (
            args.get("failover_manager") == "repmgr"
            and args.get("postgres_flavour") == "epas"
        ):
            raise ArchitectureError(
                f"TPA does not support repmgr with {args.get('postgres_flavour')}"
            )

    def num_instances(self):
        # each active location has:
        #   - the requested number of data nodes
        #   - 3 etcd nodes if this is a patroni cluster
        #   - 2 haproxy nodes if haproxy is enabled
        # and in addition, independently of the number of active locations,
        # we have:
        #   - 1 node if there is a witness-only location
        #   - 1 node if there is a single-node location
        #   - 1 barman node at the primary location

        instances_per_active_location = (
            self.args.get("data_nodes_per_location")
            + (3 if self.args.get("failover_manager") == "patroni" else 0)
            + (2 if self.args.get("enable_haproxy") else 0)
        )

        return (
            len(self.args["active_locations"]) * instances_per_active_location
            + (1 if self.args.get("witness_only_location") else 0)
            + (1 if self.args.get("single_node_location") else 0)
            + 1
        )

    def default_location_names(self):
        return ["main"]

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
            pemserver_name = (
                "%s-pemserver" % self.args["cluster_name"]
                if self.args.get("cluster_prefixed_hostnames")
                else "pemserver"
            )

            instances.append(
                {
                    "node": n + 1,
                    "Name": pemserver_name,
                    "role": ["pem-server"],
                    "location": self.args["locations"][0]["Name"],
                }
            )

    def update_cluster_vars(self, cluster_vars):
        """
        Makes architecture-specific changes to cluster_vars if required
        """
        failover_manager = self.args.get("failover_manager")
        cluster_vars.update(
            {
                "failover_manager": failover_manager,
            }
        )

        if failover_manager == "patroni":
            # Ensure nodes are members of a single etcd_location per cluster for patroni.
            cluster_vars["etcd_location"] = "main"
