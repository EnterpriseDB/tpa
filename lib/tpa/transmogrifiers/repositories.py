#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

from typing import List, Optional

from ..transmogrifier import Transmogrifier, opt
from ..changedescription import ChangeDescription
from ..checkresult import CheckResult


class Repositories(Transmogrifier):
    def __init__(self, default_repos: Optional[List[str]] = None):
        self._default_repos = default_repos or []

    @classmethod
    def options(cls):
        return {
            **opt(
                "--edb-repositories",
                nargs="+",
                help="space-separated list of EDB package repositories",
            )
        }

    def check(self, cluster):
        return CheckResult()

    def apply(self, cluster):
        cluster.vars["edb_repositories"] = self.edb_repositories(cluster)

    def description(self, cluster):
        repos = self.edb_repositories(cluster)
        return ChangeDescription(items=[f"Set edb_repositories to {repos}"])

    # XXX This function is at present suitable only for use from BDR4PGD5.
    # - we need to ensure we are given valid repositories
    # - we currently assume edb_repositories are set, this might not be true
    #   (bdr4 cluster only needing to add edb_repositories but not through BDR4PGD5)
    # - we assume postgres_flavour is set (could be postgresql for old cluster if used
    #   alone without BDR4PGD5)
    def edb_repositories(self, cluster):
        postgres_flavour = cluster.vars.get("postgres_flavour")
        postgres_repos = {
            "postgresql": ["standard"],
            "edbpge": ["standard"],
            "pgextended": ["standard"],
            "epas": ["enterprise"],
        }
        default_repos = postgres_repos[postgres_flavour] + self._default_repos

        return self.args.edb_repositories or default_repos
