#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.


from ..transmogrifier import Transmogrifier, opt
from ..changedescription import ChangeDescription
from ..checkresult import CheckResult


class Replace2qRepositories(Transmogrifier):
    def __init__(self):
        # this dict matches the one for new clusters in lib/tpaexec/architectures.py
        self.postgres_repos = {
            "postgresql": ["standard"],
            "edbpge": ["standard"],
            "pgextended": ["standard", "postgres_extended"],
            "epas": ["enterprise"],
        }

    @classmethod
    def options(cls):
        return {**opt("--replace-2q-repositories", action="store_true")}

    def is_applicable(self, cluster):
        return True
        if "edb_repositories" in cluster.vars:
            return False

        if cluster.vars.get("tpa_2q_repositories") == []:
            # this means no 2q repos at all, even those added at deploy-time
            return False

        if cluster.vars.get("postgres_flavour") not in self.postgres_repos:
            return False

        # if you have been using an explicit yum or apt repo list that doesn't include
        # PGDG, and you're not going to end up with standard or enterprise, we'd
        # better not break your cluster

        repository_list = [
            r
            for k in cluster.vars
            if k.endswith("_repository_list")
            for r in cluster.vars.get(k)
        ]
        if (
            repository_list
            and "PGDG" not in repository_list
            and not (
                self._using_closed_2q_repos(cluster) or postgres_flavour != "postgresql"
            )
        ):

            return False

    def check(self, cluster):
        cr = CheckResult()

        if "tpa_2q_repositories" not in cluster.vars:
            cr.warning("No 2q repositories present in cluster")

        bdr_version = cluster.vars.get("bdr_version")
        if bdr_version is not None and bdr_version not in ("3", "4"):
            cr.error(f"BDR version { bdr_version } cannot be upgraded (must be 3 or 4)")

        return cr

    def _using_closed_2q_repos(self, cluster):
        tpa_2q_repos = cluster.vars.get("tpa_2q_repositories")
        if tpa_2q_repos is None:
            return False
        if len([r for r in tpa_2q_repos if r != "dl/default/release"]) > 0:
            return True
        return False

    def _get_edb_repositories(self, cluster):
        edb_repositories = []

        postgres_flavour = cluster.vars.get("postgres_flavour")
        if self._using_closed_2q_repos(cluster) or postgres_flavour != "postgresql":
            edb_repositories = self.postgres_repos[postgres_flavour]

        bdr_version = cluster.vars.get("bdr_version")
        if bdr_version == "3":
            if postgres_flavour == "pgextended":
                edb_repositories.append("bdr_3_7_postgres_extended")
            elif postgres_flavour == "epas":
                edb_repositories.append("bdr_3_7_postgres_advanced")
            else:
                edb_repositories.appendd("bdr_3_7_postgres")
        elif bdr_version == "4":
            edb_repositories.append("postgres_distributed_4")

        return edb_repositories

    def apply(self, cluster):
        edb_repositories = self._get_edb_repositories(cluster)
        if edb_repositories:
            cluster.vars["edb_repositories"] = edb_repositories
        if "tpa_2q_repositories" in cluster.vars:
            del cluster.vars["tpa_2q_repositories"]

    def description(self, cluster):
        changelist = []

        edb_repositories = self._get_edb_repositories(cluster)
        if edb_repositories:
            changelist.append(
                ChangeDescription(
                    title="Add EDB repositories", items=[edb_repositories]
                )
            )

        tpa_2q_repositories = cluster.vars.get("tpa_2q_repositories")
        if tpa_2q_repositories:
            changelist.append(
                ChangeDescription(
                    title="Remove 2q repositories", items=[tpa_2q_repositories]
                )
            )

        return ChangeDescription(title="Replace repositories", items=changelist)
