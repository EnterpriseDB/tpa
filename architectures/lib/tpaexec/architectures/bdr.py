#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

from ..architecture import Architecture
from typing import List, Tuple

import sys


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
        return super().cluster_vars_args() + ["bdr_version", "bdr_node_group", "bdr_database"]

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
        postgresql_flavour = self.args.get("postgresql_flavour") or "postgresql"
        postgres_version = self.args.get("postgres_version")
        bdr_version = self.args.get("bdr_version")

        given_repositories = " ".join(tpa_2q_repositories)

        default_bdr_versions = {
            "9.4": "1",
            "9.6": "2",
            "10": "3",
            "11": "3",
            "12": "3",
            "13": "3",
            "14": "4",
            None: "3"
        }

        default_pg_versions = {
            "1": "9.4",
            "2": "9.6",
            "3": "13",
            "4": "14",
        }

        if bdr_version is None:
            bdr_version = default_bdr_versions.get(postgres_version)
        if postgres_version is None:
            postgres_version = default_pg_versions.get(bdr_version)

        if (postgres_version, bdr_version) not in self.supported_versions():
            print(
                "ERROR: Postgres %s with BDR %s is not supported"
                % (postgres_version, bdr_version),
                file=sys.stderr,
            )
            sys.exit(-1)

        extensions = []

        if bdr_version == "1":
            postgresql_flavour = "postgresql-bdr"
        elif bdr_version == "2":
            if not tpa_2q_repositories or "/bdr2/" not in given_repositories:
                tpa_2q_repositories.append("products/bdr2/release")
        elif bdr_version == "3":
            extensions = ["pglogical"]
            if not tpa_2q_repositories:
                if postgresql_flavour == "2q":
                    tpa_2q_repositories.append("products/2ndqpostgres/release")
                elif postgresql_flavour == "epas":
                    tpa_2q_repositories.append(
                        "products/bdr_enterprise_3_7-epas/release"
                    )
                else:
                    tpa_2q_repositories.append("products/bdr3_7/release")
                    tpa_2q_repositories.append("products/pglogical3_7/release")
        elif bdr_version == "4":
            if not tpa_2q_repositories or "/bdr4/" not in given_repositories:
                tpa_2q_repositories.append("products/bdr4/release")

        cluster_vars.update(
            {
                "repmgr_failover": "manual",
                "postgres_coredump_filter": "0xff",
                "bdr_version": bdr_version,
                "postgres_version": postgres_version,
                "postgresql_flavour": postgresql_flavour,
            }
        )

        if tpa_2q_repositories:
            cluster_vars.update(
                {
                    "tpa_2q_repositories": tpa_2q_repositories,
                }
            )

        if extensions:
            cluster_vars.update({"extra_postgres_extensions": extensions})

    def update_instances(self, instances):

        # If --enable-camo is specified, we collect all the instances with role
        # [bdr,primary] and no partner already set and set them pairwise to be
        # each other's CAMO partners. This is crude, but it's good enough to
        # experiment with CAMO on a two- or four-node BDR-Simple cluster.

        if self.args.get("enable_camo", False):
            bdr_primaries = []
            ins_defs = self.args["instance_defaults"]
            for i in instances:
                _vars = i.get("vars", {})
                role = i.get("role", ins_defs.get("role", []))
                if (
                    "bdr" in role
                    and "replica" not in role
                    and "readonly" not in role
                    and "subscriber-only" not in role
                    and "witness" not in role
                ):
                    if "bdr_node_camo_partner" not in _vars:
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
