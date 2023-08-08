#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.


from ..transmogrifier import Transmogrifier
from ..changedescription import ChangeDescription
from ..checkresult import CheckResult


class Common(Transmogrifier):
    """Performs assorted common functions that other Transmogrifiers can
    implicitly depend on; guaranteed to be applied first, before any other
    Transmogrifier.
    """

    def check(self, cluster):
        return CheckResult()

    def apply(self, cluster):
        # Rewrite postgresql_flavour to postgres_flavour, and change the flavour
        # from 2q to pgextended while we're at it.

        if not cluster.vars.get("postgres_flavour"):
            flavour = cluster.vars.get("postgresql_flavour")
            if flavour:
                cluster.vars["postgres_flavour"] = flavour
                del cluster.vars["postgresql_flavour"]

        if cluster.vars.get("postgres_flavour") == "2q":
            cluster.vars["postgres_flavour"] = "pgextended"

    def description(self, cluster):
        return ChangeDescription()
