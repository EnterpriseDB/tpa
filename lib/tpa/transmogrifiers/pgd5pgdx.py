#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

"""
This transmogrifier changes a PGD-Always-ON cluster running PGD version 5 to a
PGD-X cluster running PGD version 6.
"""

# --- Rationale and Migration Strategy ---
#
# This transmogrifier is the second and final step in the two-stage process
# of upgrading a PGD 5 (PGD-Always-ON) cluster configuration (config.yml)
# to that of PGD 6 (PGD-X). Its primary role is to make necessary changes
# to the config.yml for the subsequent major version upgrade, but only
# after validating that all prerequisites have been met.
#
# The Migration Strategy:
# - Prerequisite Enforcement: The transmogrifier acts as a strict gatekeeper.
#   Its `check()` and `_run_prerequisite_checks()` methods validate that the
#   cluster configuration is in a correct state for the upgrade. This includes
#   confirming that we start with PGD-Always-ON with bdr_version 5, and most
#   importantly, that the migration from pgd-proxy to the built-in
#   Connection Manager has already been completed.
#
# - Configuration Updates: Once all checks pass, the `apply()` method
#   performs the final configuration changes:
#   1.  Sets `bdr_version` to '6'.
#   2.  Sets `pgd_flavour` to 'expanded'.
#   3.  Changes the `architecture` to 'PGD-X'.
#
# - Key Remapping: As part of the cleanup, it remaps any deprecated keys
#   to their new equivalents. Specifically, it renames `enable_proxy_routing`
#   to `enable_routing` wherever it is found, ensuring a clean and valid
#   configuration for PGD 6. This may not be required at this stage
#   anyway. No harm in making sure

import sys

from ..changedescription import ChangeDescription
from ..checkresult import CheckResult
from ..exceptions import ConfigureError
from ..transmogrifier import Transmogrifier, opt
from .repositories import Repositories


class PGD5PGDX(Transmogrifier):
    """
    Upgrades a PGD-Always-ON cluster (PGD 5) to the PGD-X architecture (PGD 6).

    This transmogrifier handles the configuration changes required for the
    major version upgrade, such as updating version numbers and renaming
    deprecated keys. It is activated by the --architecture PGD-X option.
    """

    def __init__(self):
        self.require(Repositories(default_repos=["postgres_distributed"]))

    def is_applicable(self, cluster):
        return self.args.target_architecture == "PGD-X"

    def _run_prerequisite_checks(self, cluster):
        """
        Runs a series of checks to ensure the cluster is in a valid state for the upgrade.
        """
        # Alright, before we touch anything, let's make sure this cluster
        # configuration is actually in the right state for this upgrade. If
        # not, we'll stop right here.

        # First up, make sure we're coming from BDR version 5.

        # We cannot, however, reasonably tell at this stage if the cluster has
        # already been upgraded to BDR version 5.9+. That's not within the
        # scope of this transmogrifier. So we proceed under the assumption that
        # the target cluster is already running 5.9+. FWIW, we do keep a backup
        # of the original config.yml just in case ...
        current_bdr_version = cluster.vars.get("bdr_version")
        if current_bdr_version != "5":
            raise ConfigureError(
                f"Prerequisite failed: The current bdr_version must be '5' to upgrade, but it is '{current_bdr_version}'."
            )

        # We want to also make sure that the cluster has been upgraded to run
        # ConnectionManager in place of pgd-proxy. At this stage, since we do
        # not process inventory directly, we'll trust that the cluster has gone
        # through the previous step of transmogrification which would have
        # enabled the builtin connection manager by defining
        # 'bdr.enable_builtin_connection_manager' key in
        # `postgres_conf_settings`. If not, this whole thing is a no-go.

        # Does the 'postgres_conf_settings' section even exist? It could be
        # missing or just empty. We do trust that the previous step i.e.
        # PGD-Proxy → ConnectionManager would have created
        # `postgres_conf_settings` hash, however, we cannot gaurantee that no
        # other manual editing took place. So we start by validating it.

        # Let's create a helpful suggestion (to avoid repeatition) for the user
        # in case the following checks fail.
        suggestion = """
Hint: It looks like the cluster hasn't been migrated to Connection Manager yet.
Please run the following command to migrate it first:

    tpaexec reconfigure <cluster_name> --enable-connection-manager
"""

        conf_settings = cluster.vars.get("postgres_conf_settings")

        if not conf_settings or not isinstance(conf_settings, dict):
            raise ConfigureError(
                "Prerequisite failed: The 'postgres_conf_settings' section is missing or empty."
                f"{suggestion}"
            )

        # `postgres_conf_settings` is defined, but does it set
        # 'bdr.enable_builtin_connection_manager' as we expect? We could
        # possibly combine the following two checks into one, we'll be a bit
        # generous and look at the individual bits separately, eh.

        if "bdr.enable_builtin_connection_manager" not in conf_settings:
            raise ConfigureError(
                "Prerequisite failed: The key 'bdr.enable_builtin_connection_manager' is missing "
                f"from the 'postgres_conf_settings' section.{suggestion}"
            )
        # Cool, the key is there. Last check: is it actually set to 'true'?
        cm_status = conf_settings.get("bdr.enable_builtin_connection_manager")
        if str(cm_status).lower() != "true":
            raise ConfigureError(
                f"Prerequisite failed: 'bdr.enable_builtin_connection_manager' must be 'true', "
                f"but it's set to '{cm_status}'.{suggestion}"
            )

    def _remap_deprecated_options(self, cluster):
        """
        Iterates through the configuration and remaps any deprecated keys
        to their new equivalents.
        """
        # In the new version, 'enable_proxy_routing' is renamed to 'enable_routing'.
        # Let's safely try renaming it.

        bdr_node_groups = cluster.vars.get("bdr_node_groups")

        # It is totally normal for the bdr_node_groups to contain as many
        # groups as the number of locations (or maybe more?). Anyway, we
        # iterate over the whole list and do the renaming where needed.

        if bdr_node_groups and isinstance(bdr_node_groups, list):

            for group in bdr_node_groups:
                # As a safeguard, skip any item that isn't a dictionary. In PGD
                # v5 the default config that TPA generates for
                # `--pgd-proxy-routing local` results in the top level group
                # being defined but it does not have `option` defined (unlike
                # child groups)

                # XXX Is this the right outcome? Or do we still add options to
                # this group during transformation? I'll need to check with
                # PGD6 but that's for later.
                if not isinstance(group, dict):
                    continue

                options = group.get("options")

                # Is 'options' a dictionary and does it contain
                # `enable_proxy_routing` we need to rename? Important because
                # in some variations with local routing, the top level group
                # may not have options defined at all
                if isinstance(options, dict) and "enable_proxy_routing" in options:
                    options["enable_routing"] = options.pop("enable_proxy_routing")

    def check(self, cluster):
        res = CheckResult()

        source_arch = cluster.architecture
        if source_arch == "PGD-X":
            res.error("This is already a PGD-X cluster")
        elif source_arch != "PGD-Always-ON":
            res.error(f"Don't know how to convert architecture {source_arch} to PGD-X")
        bdr_version = cluster.vars.get("bdr_version")
        if bdr_version and bdr_version != "5":
            res.error(f"Don't know how to convert bdr_version from {bdr_version} to 6")

        # A pgd-proxy cluster must be converted to use the built-in Connection
        # Manager before it can be upgraded to PGD-X.
        if len(cluster.instances.with_role("pgd-proxy")) > 0:
            res.error(
                "Cannot upgrade a cluster using the legacy pgd-proxy.\n"
                "Did you run 'tpaexec reconfigure <cluster_name> --enable-connection-manager' to migrate it first?"
            )

        # We need to find the top-level BDR node group and validate it.
        # We use the 'bdr_node_group' variable as the definitive source of truth.
        top_level_group_name = cluster.vars.get("bdr_node_group")
        if not top_level_group_name:
            res.error("'bdr_node_group' is not defined in cluster_vars.")
        elif top_level_group_name != cluster.name:
            res.error(
                f"'bdr_node_group' ('{top_level_group_name}') must match the cluster_name ('{cluster.name}')."
            )
        else:
            all_node_groups = cluster.vars.get("bdr_node_groups", [])
            top_level_group = None
            for group in all_node_groups:
                if (
                    isinstance(group, dict)
                    and group.get("name") == top_level_group_name
                ):
                    top_level_group = group
                    break

            if not top_level_group:
                res.error(
                    f"The top-level group '{top_level_group_name}' specified in 'bdr_node_group' "
                    "is not defined in 'bdr_node_groups'."
                )
            elif "parent_group_name" in top_level_group:
                res.error(
                    f"The top-level group '{top_level_group_name}' must not have a 'parent_group_name'."
                )

        return res

    def apply(self, cluster):
        try:
            # Alright, let's kick things off by running all our pre-flight
            # checks. This will make sure the cluster is actually ready for
            # what's about to happen.
            self._run_prerequisite_checks(cluster)

            # Now that we have a reasonable understanding of the currnet state
            # of the cluster configuration, and it contains the basic settings
            # we need, we can proceed
            # XXX: Is this all we needed?
            cluster.vars["bdr_version"] = "6"
            cluster.vars["pgd_flavour"] = "expanded"
            cluster._architecture = self.args.target_architecture

            # We can safely go through the configuration and remap any
            # deprecated options to their new equivalents.
            self._remap_deprecated_options(cluster)

        except KeyError as e:
            raise ConfigureError(f"Configuration is missing a required key: {e}")
        except (AttributeError, TypeError) as e:
            raise ConfigureError(
                f"Configuration has an unexpected structure or data type. Error: {e}"
            )

    def description(self, cluster):
        items = [
            "Change architecture to PGD-X",
            "Change bdr_version to 6",
            "Set pgd flavour to expanded",
            "Rename deprecated pgd-proxy keys to their modern equivalents",
        ]

        return ChangeDescription(
            title="Convert PGD-Always-ON to PGD-X",
            items=items,
        )
