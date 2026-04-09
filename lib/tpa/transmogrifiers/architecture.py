#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

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
# single, authoritative owner of the `--architecture` flag. When parsed args
# are available, it instantiates the correct specialist transmogrifier based on
# the target architecture and registers it as a dependency via require(). The
# framework then handles the specialist and all its transitive dependencies
# (check, apply, describe) automatically.
#
# Trade-Off:
# The primary limitation of this pattern is that it introduces a dependency:
# any new transmogrifier that handles an architecture change *must* be
# manually registered within this dispatcher's _specialists map. However, the
# benefits of this approach are significant. It creates a single source of
# truth for all supported architecture upgrades and provides a clear, simple
# pattern for future extensions, which is a worthwhile trade-off for the added
# clarity and robustness.

from ..changedescription import ChangeDescription
from ..checkresult import CheckResult
from ..exceptions import ConfigureError
from ..transmogrifier import Transmogrifier, opt
from .bdr4pgd5 import BDR4PGD5
from .pgd5pgdx import PGD5PGDX


class Architecture(Transmogrifier):
    """Dispatches to other transmogrifiers based on architecture."""

    # Maps each target architecture to the specialist class that handles it.
    _specialists = {
        "PGD-Always-ON": BDR4PGD5,
        "PGD-X": PGD5PGDX,
    }

    @classmethod
    def options(cls):
        # This is the single, central place where all architecture-related
        # flags are defined for the reconfigure command.
        return {
            **opt(
                "--architecture",
                choices=list(cls._specialists.keys()),
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

    def set_parsed_args(self, parsed_args):
        # Once parsed args are available, we can determine the target
        # architecture and instantiate the correct specialist. We register
        # it as a dependency via require() so that the framework can handle
        # the specialist and all its transitive dependencies (check, apply,
        # describe) automatically through the required chain.
        #
        # Source architecture validation (e.g., "can't convert M1 to
        # PGD-Always-ON") is handled by each specialist's own check()
        # method, so dispatching on target_architecture alone is sufficient.
        super().set_parsed_args(parsed_args)
        target = self.args.target_architecture
        if target is not None:
            specialist_class = self._specialists.get(target)
            if specialist_class is None:
                raise ConfigureError(
                    f"No supported upgrade path for target architecture '{target}'"
                )
            specialist = specialist_class()
            specialist.set_parsed_args(parsed_args)
            self.require(specialist)

    def is_applicable(self, cluster):
        # This dispatcher's work is only relevant if the user has actually
        # passed the --architecture flag, indicating an intent to change it.
        return self.args.target_architecture is not None

    def check(self, cluster):
        # The framework handles checking the specialist and its transitive
        # dependencies through the required chain.
        return CheckResult()

    def apply(self, cluster):
        # The framework's apply queue handles the specialist and its
        # transitive dependencies through the required chain.
        pass

    def description(self, cluster):
        # Return a title-less, empty description. The framework's describe()
        # handles the specialist's description via t.required, so the
        # specialist's output surfaces at the correct nesting level.
        # We override _items to avoid the default "No changes" text.
        desc = ChangeDescription()
        desc._items = []
        return desc
