#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

"""
This transmogrifier acts as a dispatcher for handling architecture changes.
It owns the global --architecture flag and delegates work to the specialist
transmogrifiers for each specific upgrade path.
"""
# --- Why do we need this Dispatcher ---
#
# The `tpaexec` framework is designed to have a single, globally recognized
# `--architecture` flag that can be used by different transmogrifiers. However,
# the framework's test suite and help system load the options from all
# available transmogrifiers at once.
#
# The Problem:
# If multiple transmogrifiers (e.g., `bdr4pgd5.py` and `pgd5pgdx.py` or by
# extension any future additions to this list) each try to define their own
# `--architecture` option, it creates a "conflicting option string" error.
#
# The Solution:
# This `Architecture` transmogrifier acts as a central "dispatcher." It is the
# single, authoritative owner of the `--architecture` flag. Its only job is to
# inspect the cluster's source and target architecture and then delegate all
# work (`check`, `apply`, `description`) to the correct specialist
# transmogrifier. This resolves the conflict while working in harmony with the
# framework's design, creating a clean and scalable way to support multiple
# architecture upgrades.
#
# Trade-Off:
# The primary limitation of this pattern is that it introduces a dependency:
# any new transmogrifier that handles an architecture change *must* be
# manually registered within this dispatcher. However, the benefits of this
# approach are significant. It creates a single source of truth for all
# supported architecture upgrades and provides a clear, simple pattern for
# future extensions, which is a worthwhile trade-off for the added clarity
# and robustness.

from ..exceptions import ConfigureError
from ..transmogrifier import Transmogrifier, opt
from .bdr4pgd5 import BDR4PGD5
from .pgd5pgdx import PGD5PGDX


class Architecture(Transmogrifier):
    """Dispatches to other transmogrifiers based on architecture."""

    @classmethod
    def options(cls):
        # This is the single, central place where all architecture-related
        # flags are defined for the reconfigure command.
        return {
            **opt(
                "--architecture",
                choices=["PGD-Always-ON", "PGD-X"],
                dest="target_architecture",
                help="change the cluster's architecture",
            ),
            # This option is specific to the BDR4->PGD5 path, but it must be
            # defined here in the dispatcher so it's available to the user.
            **opt(
                "--pgd-proxy-routing",
                help="Configure each PGD-Proxy to route connections to a "
                "globally-elected write leader (global) or a write leader "
                "within its own location (local)",
                choices=["global", "local"],
                dest="pgd_proxy_routing",
                default=None,
            ),
        }

    def is_applicable(self, cluster):
        # This dispatcher's work is only relevant if the user has actually
        # passed the --architecture flag, indicating an intent to change it.
        return self.args.target_architecture is not None

    def check(self, cluster):
        # We're acting as a pass-through here. We ask our internal dispatcher
        # to find the right specialist for the job, and then we tell that
        # specialist to run its own `check` method.
        return self._dispatcher(cluster).check(cluster)

    def apply(self, cluster):
        # Same as above, but for the `apply` action. The dispatcher finds
        # the specialist, and we delegate the actual configuration changes
        # to that specialist's `apply` method.
        return self._dispatcher(cluster).apply(cluster)

    def description(self, cluster):
        # Again, we delegate. The detailed, user-facing description of the
        # changes will come from the specialist transmogrifier that's doing
        # the real work.
        return self._dispatcher(cluster).description(cluster)

    def _dispatcher(self, cluster):
        """
        Inspects the source and target architecture and returns the correct
        specialist transmogrifier to handle the request.
        """
        source_arch = cluster.architecture
        target_arch = self.args.target_architecture

        # This is the core routing logic. Based on the "from" and "to"
        # architectures, we instantiate the correct specialist class.
        if source_arch == "BDR-Always-ON" and target_arch == "PGD-Always-ON":
            transmogrifier = BDR4PGD5()
        elif source_arch == "PGD-Always-ON" and target_arch == "PGD-X":
            transmogrifier = PGD5PGDX()
        else:
            # As a safeguard, if we're asked to handle a transition we don't
            # have a specialist for, we raise a not-so-fancy error.
            raise ConfigureError(
                f"No supported upgrade path found for architecture change from "
                f"'{source_arch}' to '{target_arch}'."
            )

        # It's crucial that we pass the parsed command-line arguments down to
        # the specialist, so it has access to any other flags it might need.
        transmogrifier.set_parsed_args(self.args)
        return transmogrifier
