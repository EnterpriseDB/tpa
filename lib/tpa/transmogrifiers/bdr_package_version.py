#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""
Transmogrifier that owns the --bdr-package-version flag.

Applies to BDR-Always-ON, PGD-Always-ON, PGD-X, and PGD-S clusters
(see SUPPORTED_ARCHITECTURES). Pulled in as a require() of BDR4PGD5
(the BDR-Always-ON → PGD-Always-ON specialist) so that the
read_listen_port rule for PGD 5.5+ also fires when the user is moving
to PGD-Always-ON in the same command. When a future PGD-X / PGD-S
rule appears, the equivalent wiring against PGD5PGDX (or a PGD6→6
specialist) can be added then.

When a specialist is in the run, the apply queue's initial order tries
this transmogrifier first, but is_ready() defers it until the
specialist has flipped cluster.architecture to its target. See
agent-docs/TRANSMOGRIFIERS.md for the queue mechanism.

The current rules table is small: PGD 5.5+ requires read_listen_port in
default_pgd_proxy_options. PGD-X / PGD-S use connection manager rather
than pgd-proxy, and BDR-Always-ON clusters predate pgd-proxy entirely;
none of them have default_pgd_proxy_options, so the rule no-ops on
those architectures and the work reduces to recording the supplied
bdr_package_version, which drives deploy-time package selection. New
rules slot into apply() under their own version guards.
"""

from packaging.version import InvalidVersion, Version, parse

from ..changedescription import ChangeDescription
from ..checkresult import CheckResult
from ..exceptions import ConfigureError
from ..transmogrifier import Transmogrifier, opt


# Default value for the read-only proxy port. Matches the configure-side
# default of --proxy-read-only-port in lib/tpaexec/architectures/pgd_always_on.py.
DEFAULT_READ_LISTEN_PORT = 6433

# Minimum BDR package version that requires read_listen_port in
# default_pgd_proxy_options. Mirrors BDR.BDR_WITH_READ_LISTEN_PORT on the
# configure side (lib/tpaexec/architectures/bdr.py).
BDR_WITH_READ_LISTEN_PORT = "5.5"


def _package_version_at_least(version_string, minimum):
    """Return True if the major.minor in version_string >= minimum.

    Handles wildcards ('*5.3*') and epoch prefixes ('4:5.5.1'). Raises
    ConfigureError for malformed version strings. Callers must not
    pass None or an empty string.

    Duplicated from lib/tpaexec.architecture._package_version_at_least
    so that lib/tpa code follows its own exception conventions and
    does not depend on lib/tpaexec.
    """
    try:
        cleaned = version_string.replace("*", "")
        parts = cleaned.split(":", maxsplit=1)[-1].split(".")
        return parse(f"{parts[0]}.{parts[1]}") >= Version(minimum)
    except (InvalidVersion, AttributeError, IndexError, TypeError) as e:
        raise ConfigureError(f"Cannot parse package version '{version_string}'") from e


class BdrPackageVersion(Transmogrifier):
    """Records --bdr-package-version and applies version-gated config changes.

    Currently the only gated rule is: PGD 5.5+ requires read_listen_port
    in default_pgd_proxy_options. Add new rules by adding a method and
    calling it from apply() under the appropriate version guard.
    """

    @classmethod
    def options(cls):
        return {
            **opt(
                "--bdr-package-version",
                dest="bdr_package_version",
                default=None,
                help="record bdr_package_version in config.yml and apply any "
                "configuration options that the chosen version requires",
            ),
        }

    # The architectures whose clusters we know how to apply version-gated
    # options against. Both as targets of an Architecture-driven change
    # and as the cluster's current shape for standalone use. BDR-Always-ON
    # is included for minor (BDR 3.x / 4.x) upgrades; the existing rules
    # table doesn't fire on those clusters (no default_pgd_proxy_options),
    # so the work reduces to recording bdr_package_version.
    SUPPORTED_ARCHITECTURES = ("PGD-Always-ON", "PGD-X", "PGD-S", "BDR-Always-ON")

    def is_ready(self, cluster):
        # When --architecture is in flight, wait for the specialist to
        # have flipped cluster.architecture to that target. Otherwise the
        # cluster is already in its final shape, and we run as soon as
        # that shape is one we support.
        target = getattr(self.args, "target_architecture", None)
        if target is not None:
            return cluster.architecture == target
        return cluster.architecture in self.SUPPORTED_ARCHITECTURES

    def check(self, cluster):
        res = CheckResult()

        # Validate the user-supplied --bdr-package-version is parseable.
        # We don't care about the comparison result here — we just want
        # the ConfigureError that _package_version_at_least raises on a
        # malformed string, surfaced as a clean check() error rather
        # than a stack trace from apply().
        arg_version = self._arg_version()
        if arg_version is not None:
            try:
                _package_version_at_least(arg_version, BDR_WITH_READ_LISTEN_PORT)
            except ConfigureError as e:
                res.error(str(e))

        # We can do useful work whenever the cluster either is already in
        # a supported shape (standalone use) or is being transitioned
        # into one (Architecture dispatcher in flight). The specialist
        # validates whether the source→target transition is legal, so we
        # don't second-guess it — we just refuse the cases where neither
        # path applies, which would otherwise deadlock our is_ready().
        target = getattr(self.args, "target_architecture", None)
        if target in self.SUPPORTED_ARCHITECTURES:
            return res
        if cluster.architecture in self.SUPPORTED_ARCHITECTURES:
            return res
        res.error(
            "--bdr-package-version is only supported for "
            f"{', '.join(self.SUPPORTED_ARCHITECTURES)} clusters "
            f"(this cluster is {cluster.architecture})"
        )

        return res

    def apply(self, cluster):
        arg_version = self._arg_version()
        if arg_version is not None:
            cluster.vars["bdr_package_version"] = arg_version

        if self._needs_read_listen_port(cluster):
            self._apply_read_listen_port(cluster)

    def description(self, cluster):
        items = []

        arg_version = self._arg_version()
        if arg_version is not None:
            items.append(f"Set bdr_package_version to {arg_version}")

        if self._needs_read_listen_port(cluster):
            proxy_options = cluster.vars.get("default_pgd_proxy_options") or {}
            if "read_listen_port" not in proxy_options:
                items.append(
                    "Add read_listen_port to default_pgd_proxy_options "
                    f"(default {DEFAULT_READ_LISTEN_PORT}, required by PGD "
                    f"{BDR_WITH_READ_LISTEN_PORT} and later)"
                )

        return ChangeDescription(
            title="Apply BDR package version options",
            items=items,
        )

    def _needs_read_listen_port(self, cluster):
        """Return True if the cluster will end up needing read_listen_port.

        Two conditions must hold: (1) the effective bdr_package_version
        is >= 5.5 (an absent value is treated as 'latest'), and (2) the
        cluster will end up using pgd-proxy — not connection manager,
        and not BDR-Always-ON's harp-proxy. Both apply() and
        description() consult this method, so the prediction must hold
        for both the eventual cluster state (after our apply has run)
        and the description-time view of it.

        Raises ConfigureError if the effective version string can't be
        parsed. check() catches that early for an arg supplied on the
        command line; here we let it propagate so a malformed value
        that slipped through (e.g. hand-edited into config.yml) surfaces
        cleanly during apply() or --describe rather than being silently
        treated as 'latest'.
        """
        if not self._will_use_pgd_proxy(cluster):
            return False
        effective = self._arg_version() or cluster.vars.get("bdr_package_version")
        if effective is None:
            return True
        return _package_version_at_least(effective, BDR_WITH_READ_LISTEN_PORT)

    def _will_use_pgd_proxy(self, cluster):
        """Return True if the cluster will use pgd-proxy after apply.

        PGD-X and PGD-S are connection-manager-only architectures.
        BDR-Always-ON uses harp-proxy, not pgd-proxy. PGD-Always-ON
        uses pgd-proxy unless it has been migrated to connection
        manager — the source of truth being
        bdr.enable_builtin_connection_manager in postgres_conf_settings,
        which PgdproxyCM.apply() flips on. PGD 5.9+ clusters may or may
        not have been migrated yet.
        """
        final_arch = (
            getattr(self.args, "target_architecture", None) or cluster.architecture
        )
        if final_arch != "PGD-Always-ON":
            # BDR-Always-ON uses harp-proxy; PGD-X / PGD-S are CM-only;
            # anything else has no pgd-proxy to speak of either.
            return False
        conf = cluster.vars.get("postgres_conf_settings") or {}
        cm = conf.get("bdr.enable_builtin_connection_manager")
        return str(cm).lower() != "true"

    def _apply_read_listen_port(self, cluster):
        """Ensure read_listen_port is set in default_pgd_proxy_options.

        If default_pgd_proxy_options is missing (e.g. a cluster that had
        no harp-proxy / pgd-proxy instances) we silently skip the rule
        rather than synthesise the dict ourselves.
        """
        proxy_options = cluster.vars.get("default_pgd_proxy_options")
        if not isinstance(proxy_options, dict):
            return
        proxy_options.setdefault("read_listen_port", DEFAULT_READ_LISTEN_PORT)

    def _arg_version(self):
        """Return the user-supplied --bdr-package-version value, or None."""
        return getattr(self.args, "bdr_package_version", None)
