#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 205-2025 - All rights reserved.

"""
This transmogrifier changes a PGD-Always-ON cluster running PGD version 5
from using pgd-proxy to Connection Manager(PGD 5.9+)
"""
# --- Rationale and Migration Strategy ---
#
# This transmogrifier handles the complex task of migrating a PGD 5 cluster's
# configuration from using the external pgd-proxy service to the modern,
# built-in Connection Manager. The logic must account for several variations
# in the source configuration file (config.yml).
#
# 1. Global vs. Local Routing Modes:
#    - Global Routing: `enable_proxy_routing` is defined once in the top-level
#      parent bdr_node_group.
#    - Local Routing: `enable_proxy_routing` is defined in each of the subgroups,
#      and the parent group does not have an `options` block.
#
# 2. Global Defaults vs. Per-Instance Overrides:
#    - Global settings (like `default_pgd_proxy_options`) are defined in
#      `cluster_vars` and serve as the base for the migration.
#    - Per-instance settings (`pgd_proxy_options`, `pgd_http_options`) can
#      override these defaults on specific nodes. This presents a challenge,
#      as the new Connection Manager settings are group-based, not instance-based.
#
# 3. What is Not Migrated (`bdr_node_options`):
#    - Settings like `route_priority` under `bdr_node_options` are fundamental
#      to the BDR node itself and remain valid for the built-in Connection
#      Manager. These are intentionally left untouched.
#
# The Migration Strategy:
# - The transmogrifier uses a "trigger-based" approach. It first determines
#   the routing mode (Global or Local) and then applies settings based on
#   that mode.
# - It migrates global default settings (ports, etc.) only into the group(s)
#   that have routing enabled.
# - It differentiates its logic based on the detected routing mode:
#   - In Global Routing mode, the top-level group is configured with both
#     `enable_raft: true` and `enable_routing: true`. All of its subgroups are
#     then explicitly set to `enable_routing: false`, while `enable_raft` is
#     enabled (respecting any pre-existing `false` values).
#   - In Local Routing mode, the state of the top-level group is made explicit
#     (typically `enable_raft: true`, `enable_routing: false`).
# - For backward compatibility, it preserves the original `enable_proxy_routing`
#   key, copying its value to the new `enable_routing` key. The legacy key
#   is removed in the subsequent upgrade to PGD-X.
# - A final corrective pass is made to enforce a critical PGD 5.9+ rule:
#   if any subgroup ends up with both `enable_routing: false` and
#   `enable_raft: false`, it forces `enable_raft` to `true`.
# - It detects per-instance overrides, prints a clear WARNING, and safely
#   removes the obsolete instance-level keys.
import sys

from ..changedescription import ChangeDescription
from ..checkresult import CheckResult
from ..exceptions import ConfigureError
from ..transmogrifier import Transmogrifier, opt
from .repositories import Repositories


class PgdproxyCM(Transmogrifier):
    """
    Migrates a PGD-Always-ON cluster from using the legacy pgd-proxy
    to the built-in Connection Manager.

    This is a prerequisite step before upgrading a PGD 5 cluster to PGD 6.
    It is activated by the --enable-connection-manager flag.
    """

    def __init__(self):
        self.require(Repositories(default_repos=["postgres_distributed"]))

    @classmethod
    def options(cls):
        return {
            **opt(
                "--enable-connection-manager",
                action="store_true",
                help="change the cluster to use Connection Manager",
            ),
        }

    def is_applicable(self, cluster):
        # This only applies if the user passes the --enable-connection-manager flag.
        return self.args.enable_connection_manager

    def check(self, cluster):
        res = CheckResult()

        if cluster.architecture != "PGD-Always-ON":
            res.error("This transmogrifier only supports PGD-Always-ON clusters")

        if len(cluster.instances.with_role("pgd-proxy").without_role("bdr")) > 0:
            res.error("Proxy instances must also be BDR instances")

        # Let's make sure the cluster hasn't already been migrated. We'll check
        # if the Connection Manager setting is already set to 'true'. Of course
        # there is no evidence is our scope yet to confirm whether or not the
        # migration has actually happened on the target cluster. We deal with
        # the `config.yml` at this stage and that's what we will stick to to
        # base our decisions.
        conf_settings = cluster.vars.get("postgres_conf_settings", {})
        cm_status = conf_settings.get("bdr.enable_builtin_connection_manager")
        if str(cm_status).lower() == "true":
            res.error(
                "This cluster already has Connection Manager enabled; "
                "this migration step is not necessary."
            )

        all_node_groups = cluster.vars.get("bdr_node_groups", [])

        # Validate for explicit conflicts in the raft/routing dependency.
        # We only fail if routing is enabled but raft is EXPLICITLY disabled.
        for group in all_node_groups:
            if not isinstance(group, dict):
                continue

            options = group.get("options", {})
            if not isinstance(options, dict):
                continue

            is_routing_enabled = (
                str(options.get("enable_proxy_routing")).lower() == "true"
            )
            # Only consider it an error if 'enable_raft' is present and false.
            is_raft_disabled = (
                "enable_raft" in options
                and str(options.get("enable_raft")).lower() == "false"
            )

            if is_routing_enabled and is_raft_disabled:
                group_name = group.get("name", "Unnamed Group")
                res.error(
                    f"In bdr_node_group '{group_name}', 'enable_proxy_routing' cannot be true "
                    "when 'enable_raft' is explicitly set to false."
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

    def _migrate_proxy_options(self, cluster):
        """
        Iterates through all node groups and migrates proxy settings to any
        group that enables routing, collecting warnings about instance-level
        overrides. Returns a list of warning messages.
        """
        warnings = []
        # Define the rename mapping for old proxy settings.
        option_renames = {
            "listen_port": "read_write_port",
            "read_listen_port": "read_only_port",
        }

        all_node_groups = cluster.vars.get("bdr_node_groups", [])
        if not all_node_groups or not isinstance(all_node_groups, list):
            return warnings

        # We need to detect the routing mode to correctly handle the state of
        # the top-level group vs. the subgroups.
        local_routing_detected = False
        global_routing_detected = False
        top_level_group_name = cluster.vars.get("bdr_node_group")

        for group in all_node_groups:
            if not isinstance(group, dict):
                continue

            options = group.get("options")
            if isinstance(options, dict) and "enable_proxy_routing" in options:
                is_routing_enabled = (
                    str(options.get("enable_proxy_routing")).lower() == "true"
                )

                # For backward compatibility, we copy the value to the new key
                # but leave the original 'enable_proxy_routing' key intact for now.
                options["enable_routing"] = options["enable_proxy_routing"]

                if is_routing_enabled:
                    # If routing is enabled, we infer that raft must also be enabled.
                    options["enable_raft"] = True

                    # Check if this is a subgroup or the top-level group to
                    # determine the routing mode.
                    if "parent_group_name" in group:
                        local_routing_detected = True
                    elif group.get("name") == top_level_group_name:
                        global_routing_detected = True

                    # Move and rename the GLOBAL port settings into this group.
                    proxy_options = cluster.vars.get("default_pgd_proxy_options", {})
                    for old, new in option_renames.items():
                        if old in proxy_options:
                            options[new] = proxy_options[old]

                    # Move and handle the GLOBAL http options.
                    http_options = cluster.vars.get("pgd_http_options", {})
                    if "port" in http_options:
                        options["http_port"] = http_options["port"]
                    if "secure" in http_options:
                        options["use_https"] = http_options["secure"]

        # In local routing mode, the top-level group often has no options.
        # It's better to make its state explicit.
        if local_routing_detected:
            top_level_group = None
            for group in all_node_groups:
                if group.get("name") == top_level_group_name:
                    top_level_group = group
                    break
            if top_level_group:
                top_level_options = top_level_group.setdefault("options", {})
                if "enable_raft" not in top_level_options:
                    top_level_options["enable_raft"] = True
                if "enable_routing" not in top_level_options:
                    top_level_options["enable_routing"] = False

        # In global routing mode, we must explicitly set the state for all subgroups.
        if global_routing_detected:
            for group in all_node_groups:
                # We are only interested in subgroups, which must have a parent.
                if isinstance(group, dict) and "parent_group_name" in group:
                    sub_options = group.setdefault("options", {})
                    # Subgroups need to manage their own Raft consensus for local HA,
                    # so we enable it unless it was explicitly disabled (e.g. for a witness).
                    if "enable_raft" not in sub_options:
                        sub_options["enable_raft"] = True
                    sub_options["enable_routing"] = False

        # Corrective pass: PGD 5.9+ requires that a group cannot have both
        # routing and raft disabled. We enforce this here as a final step.
        for group in all_node_groups:
            if not isinstance(group, dict) or "parent_group_name" not in group:
                continue

            options = group.get("options", {})
            is_routing_false = (
                str(options.get("enable_routing", "false")).lower() == "false"
            )
            is_raft_false = str(options.get("enable_raft", "false")).lower() == "false"

            if is_routing_false and is_raft_false:
                options["enable_raft"] = True

        # Now, check for and collect warnings about any per-instance overrides
        for instance in cluster.instances:
            for section in ["pgd_proxy_options", "pgd_http_options"]:
                if section in instance.host_vars:
                    warnings.append(
                        f"Instance '{instance.name}' has local '{section}' defined, "
                        "which cannot be automatically migrated. Please review "
                        "and migrate these settings manually."
                    )
                    # Clean up the obsolete key from the instance's host_vars.
                    instance.host_vars.pop(section, None)

        # Clean up all old and now-obsolete GLOBAL proxy sections from cluster_vars.
        # We do this once, after all processing is finished.
        for section in [
            "default_pgd_proxy_options",
            "pgd_proxy_options",
            "pgd_http_options",
        ]:
            cluster.vars.pop(section, None)

        return warnings

    def apply(self, cluster):
        try:
            # We only care about PGD 5 to support migration to the Connection
            # Manager.
            if cluster.vars.get("bdr_version") != "5":
                raise ConfigureError(
                    "BDR version must be 5 to convert to Connection Manager"
                )

            # XXX: This could potentially need some revisting since PGD 5 has
            # known support for non-cohosted proxy instances. That's
            # potentially a problem because:
            # a) We don't yet know what we can reasonably do with the left-over
            # proxy instances once migration to the connection manager is
            # complete
            # b) It could also mean change in the application stack for the
            # change in the connection to point to new IPs. This is not a TPA
            # issue; still something to consider though.

            # Is there anything that the transmogrification process can do
            # about 'b'? Unfortunately NO.

            # This transmogrifier's responsibility is to migrate the
            # configuration from pgd-proxy to Connection Manager. Removing the
            # role is a key part of this migration. Any dependencies in
            # subsequent upgrade commands should account for this change in the
            # cluster's state.
            for i in cluster.instances.with_role("pgd-proxy"):
                i.remove_role("pgd-proxy")

            # Move and rename all the old proxy settings.
            warnings = self._migrate_proxy_options(cluster)

            # Finally, enable the built-in Connection Manager via GUC.
            conf_settings = cluster.vars.setdefault("postgres_conf_settings", {})
            conf_settings["bdr.enable_builtin_connection_manager"] = "true"

            # After all changes are applied, print any warnings we collected.
            if warnings:
                print("\n--- Manual Action Required ---")
                for warning in warnings:
                    print(f"WARNING: {warning}")
                print("------------------------------")

        except (KeyError, AttributeError, TypeError) as e:
            raise ConfigureError(
                f"Configuration has an unexpected structure or data type. Error: {e}"
            )

    def description(self, cluster):
        items = [
            "Remove pgd-proxy role",
            "Change pgd-proxy options to Connection Manager options",
            "Enable Connection Manager via GUC",
        ]

        return ChangeDescription(
            title="Convert pgd-proxy to Connection Manager",
            items=items,
        )
