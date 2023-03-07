#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

from ..architecture import Architecture
from ..exceptions import BDRArchitectureError
from typing import List, Tuple
import re


class BDR(Architecture):
    def supported_versions(self) -> List[Tuple[str, str]]:
        """
        Returns a list of (postgres_version, bdr_version) tuples that this
        architecture supports. Meant to be implemented by subclasses.
        """
        return []

    def bdr_major_versions(self) -> List[str]:
        """
        Returns a list of BDR major versions supported by this architecture.
        """
        return list(set(map(lambda t: t[1], self.supported_versions())))

    def add_architecture_options(self, p, g):
        g.add_argument(
            "--bdr-version",
            metavar="VER",
            help="major version of BDR required",
            dest="bdr_version",
            choices=self.bdr_major_versions(),
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
        return super().cluster_vars_args() + [
            "bdr_version",
            "bdr_database",
            "harp_consensus_protocol",
        ]

    def update_cluster_vars(self, cluster_vars):
        # We must decide which version of Postgres to install, which version
        # of BDR to install, and which repositories and extensions must be
        # enabled for the combination to work.
        #
        # If --postgres-version is specified, we infer the correct BDR
        # version. If --bdr-version is specified, we infer the correct
        # Postgres version. If both are specified, we check that the
        # combination makes sense.
        #
        # If any --2Q-repositories are specified, we do not interfere with
        # that setting at all.

        tpa_2q_repositories = self.args.get("tpa_2q_repositories") or []
        postgres_flavour = self.args.get("postgres_flavour")
        postgres_version = self.args.get("postgres_version")
        bdr_version = self.args.get("bdr_version")
        harp_enabled = self.args.get("failover_manager") == "harp"

        given_repositories = " ".join(tpa_2q_repositories)

        arch = self.args["architecture"]
        default_bdr_versions = {
            "9.4": "1",
            "9.6": "2",
            "10": "3",
            "11": "3",
            "12": "5" if arch == "PGD-Always-ON" else "4",
            "13": "5" if arch == "PGD-Always-ON" else "4",
            "14": "5" if arch == "PGD-Always-ON" else "4",
            "15": "5" if arch == "PGD-Always-ON" else "4",
            None: "5" if arch == "PGD-Always-ON" else "4",
        }

        default_pg_versions = {
            "1": "9.4",
            "2": "9.6",
            "3": "13",
            "4": "14",
            "5": "15",
        }

        if bdr_version is None:
            bdr_version = default_bdr_versions.get(postgres_version)
        if postgres_version is None:
            postgres_version = default_pg_versions.get(bdr_version)

        if (postgres_version, bdr_version) not in self.supported_versions():
            raise BDRArchitectureError(
                f"Postgres {postgres_version} with BDR {bdr_version} is not supported"
            )

        extensions = []

        if bdr_version == "1":
            postgres_flavour = "postgresql-bdr"
        elif bdr_version == "2":
            if not tpa_2q_repositories or "/bdr2/" not in given_repositories:
                tpa_2q_repositories.append("products/bdr2/release")
        elif bdr_version == "3":
            extensions = ["pglogical"]
            if not tpa_2q_repositories:
                if postgres_flavour == "pgextended":
                    tpa_2q_repositories.append("products/bdr_enterprise_3_7/release")
                elif postgres_flavour == "epas":
                    tpa_2q_repositories.append(
                        "products/bdr_enterprise_3_7-epas/release"
                    )
                else:
                    tpa_2q_repositories.append("products/bdr3_7/release")
                    tpa_2q_repositories.append("products/pglogical3_7/release")
        elif bdr_version == "4":
            if not tpa_2q_repositories or "/bdr4/" not in given_repositories:
                tpa_2q_repositories.append("products/bdr4/release")
            if postgres_flavour == "pgextended" and (
                not tpa_2q_repositories or "/2ndqpostgres/" not in given_repositories
            ):
                tpa_2q_repositories.append("products/2ndqpostgres/release")

        # bdr5 is in EBD CS repositories

        if harp_enabled and (
            not tpa_2q_repositories or "/harp/" not in given_repositories
        ):
            tpa_2q_repositories.append("products/harp/release")

        cluster_vars.update(
            {
                "postgres_coredump_filter": "0xff",
                "bdr_version": bdr_version,
                "postgres_version": postgres_version,
                "postgres_flavour": postgres_flavour,
            }
        )

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

        if extensions:
            cluster_vars.update({"extra_postgres_extensions": extensions})

        # The node group name used to be configurable, but it's now hardcoded to
        # match the cluster name, because harp/pgdcli/pgd-proxy depend on their
        # cluster name setting matching the node group name.
        self.args["bdr_node_group"] = self.bdr_safe_name(self.cluster_name())
        cluster_vars.update({"bdr_node_group": self.args["bdr_node_group"]})

    def bdr_safe_name(self, name):
        """
        Return a string containing the given name with all uppercase characters
        transformed to lowercase, and any other characters outside [a-z0-9_-]
        transformed to _, for use as the name of a BDR node, group, etc.

        See bdr_functions.c:is_valid_bdr_name()
        """
        return re.sub("[^a-z0-9_-]", "_", name.lower())

    def update_instances(self, instances):

        self._update_instance_camo(instances)
        self._update_instance_pem(instances)

    def _instance_roles(self, instance):
        """
        Returns a set of role names for the given instance, which includes roles
        set directly on the instance, as well as any roles in instance_defaults.
        """
        ins_defs = self.args["instance_defaults"]
        return set(instance.get("role", ins_defs.get("role", [])))

    def _instance_location(self, instance):
        """
        Returns the location setting for the given instance, which may be
        inherited from instance_defaults instead of being set on the instance.
        """
        ins_defs = self.args["instance_defaults"]
        return instance.get("location", ins_defs.get("location"))

    @property
    def _readonly_bdr_roles(self):
        """
        Returns a set of role names, any of which, if present on a BDR instance,
        indicate that it is not a primary instance.
        """
        return {
            "replica",
            "readonly",
            "subscriber-only",
            "witness",
        }

    def _is_bdr_primary(self, instance):
        """
        Returns true if the given instance is a BDR primary, false otherwise.

        At this stage, a BDR primary would not have "primary" in its role, so it
        is a BDR instance that has none of the roles that would identify it as a
        not-primary instance.
        """
        roles = self._instance_roles(instance)
        return "bdr" in roles and not roles & self._readonly_bdr_roles

    def _update_instance_camo(self, instances):
        """
        If --enable-camo is specified, we collect all the instances with role
        [bdr,primary] and no partner already set and set them pairwise to be
        each other's CAMO partners. This is crude, but it's good enough to
        experiment with CAMO.
        """
        if self.args.get("enable_camo", False):
            bdr_primaries = []
            for instance in instances:
                _vars = instance.get("vars", {})
                if (
                    self._is_bdr_primary(instance)
                    and "bdr_node_camo_partner" not in _vars
                ):
                    bdr_primaries.append(instance)

            idx = 0
            while idx + 1 < len(bdr_primaries):
                a = bdr_primaries[idx]
                b = bdr_primaries[idx + 1]

                # Don't assign instances in different locations to be each
                # other's partner, just skip this pair and see if there are
                # other possible matches.
                if self._instance_location(a) != self._instance_location(b):
                    idx += 1
                    continue

                a_vars = a.get("vars", {})
                a_vars["bdr_node_camo_partner"] = b.get("Name")
                a["vars"] = a_vars

                b_vars = b.get("vars", {})
                b_vars["bdr_node_camo_partner"] = a.get("Name")
                b["vars"] = b_vars

                idx += 2

    def _update_instance_pem(self, instances):
        """
        Add pem-agent to instance roles where applicable.

        If --enable-pem is specified, we add the 'pem-agent' role to BDR and
        Barman instances, and add a dedicated 'pemserver' instance to host the
        PEM server.
        """
        if self.args.get("enable_pem", False):

            for instance in instances:
                if "bdr" in self._instance_roles(instance):
                    instance["role"].append("pem-agent")

                if "barman" in self._instance_roles(instance) and self.args.get(
                    "enable_pg_backup_api", False
                ):
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
