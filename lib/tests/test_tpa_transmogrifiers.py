#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""Tests for transmogrifier implementation object."""

from argparse import ArgumentParser, Namespace
import pytest

from tpa.cluster import Cluster
from tpa.exceptions import ConfigureError
from tpa.transmogrifier import apply as apply_queue
from tpa.transmogrifiers import (
    BDR4PGD5,
    PGD5PGDX,
    BdrPackageVersion,
    Repositories,
    Replace2qRepositories,
    Common,
    Architecture,
    transmogrifiers_from_args,
    add_all_transmogrifier_options,
)
from tpa.transmogrifiers.bdr_package_version import (
    BDR_WITH_READ_LISTEN_PORT,
    DEFAULT_READ_LISTEN_PORT,
    _package_version_at_least,
)


class TestTransmogrifiers:
    """test suite for Transmogrifiers"""

    @pytest.mark.parametrize(
        "args, error, expected",
        [
            (["--architecture", "PGD-Always-ON"], None, [Common, Architecture]),
            (["--edb-repositories", "dev"], None, [Common, Repositories]),
            (
                [
                    "--architecture",
                    "PGD-Always-ON",
                    "--pgd-proxy-routing",
                    "local",
                    "--edb-repositories",
                    "dev",
                ],
                None,
                [Common, Architecture],
            ),
            (
                ["--bdr-package-version", "5.5.0"],
                None,
                [Common, BdrPackageVersion],
            ),
            (
                [
                    "--architecture",
                    "PGD-Always-ON",
                    "--bdr-package-version",
                    "5.5.0",
                ],
                None,
                # BdrPackageVersion is required by BDR4PGD5 (via Architecture),
                # so it dedups out of the top-level list — its parsed args
                # still reach the required instance via set_parsed_args.
                [Common, Architecture],
            ),
            ([], None, []),
        ],
    )
    def test_transmogrifiers_from_args(self, args, error, expected):
        """test transmogrifiers_from_args function"""
        if error:
            with pytest.raises(error):
                assert transmogrifiers_from_args(args)
        else:
            assert [type(x) for x in transmogrifiers_from_args(args)] == expected

    def test_transmogirfiers_add_all_transmogrifier_options(self):
        """test add_all_transmogrifier_options function"""
        p = ArgumentParser()
        add_all_transmogrifier_options(p)

    def test_transmogrifiers_from_args_specialist_owns_its_repositories(self):
        """Architecture's specialist owns its Repositories dependency

        This verifies the structural invariant the dedup relies on: when the
        user requests both --architecture and --edb-repositories, the
        specialist's Repositories instance (which carries PGD-specific
        default_repos) appears in Architecture's all_required() after dedup.
        The user's --edb-repositories value still reaches this instance
        through set_parsed_args, so it is NOT dropped — it's applied by the
        specialist's Repositories rather than by a separate standalone one.
        """
        result = transmogrifiers_from_args(
            [
                "--architecture",
                "PGD-Always-ON",
                "--edb-repositories",
                "dev",
            ]
        )
        # Architecture is in the list and owns a Repositories in its
        # dependency chain (via the specialist).
        architecture = next(t for t in result if isinstance(t, Architecture))
        required_classes = [type(t) for t in architecture.all_required()]
        assert Repositories in required_classes
        # The owning Repositories instance has received the user's
        # --edb-repositories value through set_parsed_args propagation.
        repos = next(
            t for t in architecture.all_required() if isinstance(t, Repositories)
        )
        assert repos.args.edb_repositories == ["dev"]

    def test_transmogrifiers_from_args_standalone_repositories_preserved(self):
        """Repositories is preserved when no other transmogrifier requires it

        When --edb-repositories is passed without --architecture, there's no
        Architecture dispatcher to claim ownership of Repositories, so the
        dedup must not filter it out — otherwise the user's input would
        have nowhere to land.
        """
        result = transmogrifiers_from_args(["--edb-repositories", "dev"])
        assert [type(t) for t in result] == [Common, Repositories]


class TestApplyQueue:
    """test suite for the framework apply queue behaviour"""

    def test_apply_queue_marks_transmogrifiers_as_applied(self, basic_bdr_cluster):
        """apply() sets _applied = True on each transmogrifier after it runs

        This is the mechanism that lets is_ready() checks tell whether a
        dependency has already been processed. Without this flag being set,
        specialists that rely on `getattr(req, "_applied", False)` would
        never see their dependencies as ready, and the queue would fail
        with "no Transmogrifier ready to apply".
        """
        # A minimal applicable scenario: --edb-repositories applies
        # Repositories against a cluster with postgres_flavour set (required
        # by Repositories._unified_repos when no edb_repositories is in vars).
        basic_bdr_cluster.vars["postgres_flavour"] = "postgresql"
        tlist = transmogrifiers_from_args(["--edb-repositories", "standard"])
        apply_queue(basic_bdr_cluster, tlist)
        # After applying, every transmogrifier in the queue must have
        # _applied set so downstream is_ready() checks can rely on it.
        for t in tlist:
            assert (
                getattr(t, "_applied", False) is True
            ), f"{type(t).__name__} was not marked as applied"


@pytest.fixture
def basic_bdr_cluster():
    return Cluster("basic", "BDR-Always-ON", "docker")


@pytest.fixture
def basic_pgd_cluster():
    return Cluster("basic", "PGD-Always-ON", "docker")


@pytest.fixture
def basic_m1_cluster():
    return Cluster("basic", "M1", "docker")


class TestReplace2qRepositories:
    """tests for Replace2qRepositories transmogrifier"""

    @pytest.mark.parametrize(
        "tpa_2q_repositories, edb_repositories, extra_repositories, postgres_flavour, expected",
        [
            (None, ["standard"], None, "epas", False),
            ([], None, None, "edbpge", False),
            (None, None, None, "epas", True),
            (None, None, ["myrepo"], "postgresql", False),
            (None, None, None, "invalid_flavour", False),
        ],
    )
    def test_replace2qrepositories_is_applicable(
        self,
        tpa_2q_repositories,
        edb_repositories,
        extra_repositories,
        postgres_flavour,
        expected,
    ):
        """test is_applicable function"""
        x = Replace2qRepositories()
        cls = Cluster("test", "BDR-Always-ON", "docker")
        if tpa_2q_repositories is not None:
            cls.vars["tpa_2q_repositories"] = tpa_2q_repositories
        if edb_repositories is not None:
            cls.vars["edb_repositories"] = edb_repositories
        if extra_repositories is not None:
            cls.vars["yum_repository_list"] = extra_repositories
        cls.vars["postgres_flavour"] = postgres_flavour

        assert x.is_applicable(cls) == expected

    def test_replace2qrepositories_check(self):
        """test check function"""
        x = Replace2qRepositories()
        cls = Cluster("test", "PGD-Always-ON", "docker")
        cls.vars["bdr_version"] = "5"

        assert len(x.check(cls).errors) == 1

    @pytest.mark.parametrize(
        "bdr_version, postgres_flavour, tpa_2q_repositories, expected",
        [
            (
                "3",
                "pgextended",
                None,
                ["bdr_3_7_postgres_extended", "standard", "postgres_extended"],
            ),
            (
                "3",
                "epas",
                None,
                ["bdr_3_7_postgres_advanced", "enterprise"],
            ),
            (
                "3",
                "postgresql",
                ["products/bdr/release"],
                ["bdr_3_7_postgres", "standard"],
            ),
            (
                None,
                "postgresql",
                ["products/dl/release"],
                ["standard"],
            ),
            (
                "4",
                "pgextended",
                ["products/bdr4/release"],
                ["postgres_distributed_4", "standard", "postgres_extended"],
            ),
            ("4", "epas", None, ["postgres_distributed_4", "enterprise"]),
            (None, "postgresql", None, None),
        ],
    )
    def test_replace2q_repositories_apply(
        self, bdr_version, postgres_flavour, tpa_2q_repositories, expected
    ):
        """test apply function"""
        x = Replace2qRepositories()
        cls = Cluster("test", "test", "docker")
        if bdr_version is not None:
            cls.vars["bdr_version"] = bdr_version
        cls.vars["postgres_flavour"] = postgres_flavour
        if tpa_2q_repositories is not None:
            cls.vars["tpa_2q_repositories"] = tpa_2q_repositories

        x.apply(cls)

        assert ("edb_repositories" not in cls.vars and expected is None) or (
            (cls.vars.get("edb_repositories") is None)
            or set(cls.vars.get("edb_repositories")) == set(expected)
        )


class TestArchitecture:
    """test suite for Architecture class"""

    def test_architecture_options(self):
        """Architecture owns both --architecture and --pgd-proxy-routing flags

        These must be defined centrally in the dispatcher to avoid conflicts
        between specialists that would otherwise each declare their own
        --architecture option.
        """
        assert "--architecture" in Architecture.options()
        assert "--pgd-proxy-routing" in Architecture.options()

    def test_architecture_options_choices_match_specialists(self):
        """--architecture choices are derived from the _specialists map

        Adding a new specialist to _specialists should automatically expose
        its target architecture as a valid --architecture choice, without
        needing to update the option definition separately.
        """
        choices = Architecture.options()["--architecture"]["choices"]
        assert set(choices) == set(Architecture._specialists.keys())

    def test_architecture_set_parsed_args_no_target(self):
        """No specialist is registered when --architecture is not passed

        If the user doesn't request an architecture change, set_parsed_args
        should not create or register any specialist. Architecture.required
        must remain empty so the transmogrifier is effectively inert.
        """
        x = Architecture()
        x.set_parsed_args(Namespace(target_architecture=None))
        assert x.required == []

    @pytest.mark.parametrize(
        "target, specialist_class",
        [
            ("PGD-Always-ON", BDR4PGD5),
            ("PGD-X", PGD5PGDX),
        ],
    )
    def test_architecture_set_parsed_args_registers_specialist(
        self, target, specialist_class
    ):
        """The correct specialist is registered based on target architecture

        This is the core dispatch behaviour: set_parsed_args must instantiate
        the specialist class matching the --architecture target and register
        it via require() so the framework sees it in the dependency tree.
        """
        x = Architecture()
        x.set_parsed_args(Namespace(target_architecture=target))
        assert len(x.required) == 1
        assert isinstance(x.required[0], specialist_class)

    def test_architecture_set_parsed_args_propagates_to_specialist(self):
        """Specialist and its transitive dependencies receive parsed args

        When Architecture registers a specialist, it must also propagate the
        parsed args down the dependency chain so that the specialist and its
        own required transmogrifiers (e.g. Repositories) can access the same
        command-line values via self.args.
        """
        x = Architecture()
        args = Namespace(target_architecture="PGD-Always-ON", edb_repositories=None)
        x.set_parsed_args(args)
        specialist = x.required[0]
        assert specialist.args is args
        # The specialist's own required (Repositories) should also have args set.
        assert specialist.required[0].args is args

    def test_architecture_set_parsed_args_all_required_includes_transitive(self):
        """all_required() surfaces the specialist and its transitive deps

        The fix's primary goal: after dispatch, Architecture.all_required()
        must expose the full dependency tree (specialist + Repositories +
        anything deeper) so the framework's check/apply/describe queues and
        the deduplication logic in transmogrifiers_from_args() can see them.
        """
        x = Architecture()
        x.set_parsed_args(Namespace(target_architecture="PGD-Always-ON"))
        required_classes = [type(t) for t in x.all_required()]
        assert BDR4PGD5 in required_classes
        assert Repositories in required_classes

    def test_architecture_is_applicable(self, basic_bdr_cluster):
        """is_applicable returns True only when --architecture is passed

        Architecture should be inert (is_applicable=False) when the user
        hasn't requested an architecture change, so the framework skips it
        during check/apply/describe.
        """
        x = Architecture()
        x._args = Namespace(target_architecture=None)
        assert x.is_applicable(basic_bdr_cluster) is False
        x._args = Namespace(target_architecture="PGD-Always-ON")
        assert x.is_applicable(basic_bdr_cluster) is True

    def test_architecture_check_returns_empty(self, basic_bdr_cluster):
        """Architecture.check() defers to the framework via required chain

        Architecture is a pure dispatcher — it has nothing to validate on
        its own. The framework's top-level check() processes the specialist
        (and its Repositories) through Architecture.required, so
        Architecture.check() itself must return an empty CheckResult to
        avoid either double-processing or adding spurious findings.
        """
        x = Architecture()
        x.set_parsed_args(Namespace(target_architecture="PGD-Always-ON"))
        result = x.check(basic_bdr_cluster)
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_architecture_apply_is_noop(self, basic_bdr_cluster):
        """Architecture.apply() is a no-op; specialist handled by framework queue

        The framework's apply queue expands all_required() and processes the
        specialist and Repositories directly. Architecture.apply() must not
        also apply them manually, or they would run twice. This verifies
        that Architecture.apply() makes no changes to the cluster.
        """
        x = Architecture()
        x.set_parsed_args(
            Namespace(target_architecture="PGD-Always-ON", pgd_proxy_routing=None)
        )
        before = dict(basic_bdr_cluster.vars)
        x.apply(basic_bdr_cluster)
        # No direct mutations from Architecture itself.
        assert dict(basic_bdr_cluster.vars) == before

    def test_architecture_description_empty(self, basic_bdr_cluster):
        """Architecture.description() returns title-less empty description

        The framework's describe() prepends descriptions from t.required to
        the parent's _items. If Architecture.description() returned the
        specialist's description directly, it would appear twice in the
        output. The empty, title-less description lets the specialist's
        output surface at the correct nesting level via t.required.
        """
        x = Architecture()
        x.set_parsed_args(Namespace(target_architecture="PGD-Always-ON"))
        desc = x.description(basic_bdr_cluster)
        assert desc._items == []
        assert desc._title is None


class TestBDR4PGD5:
    """test suite for BDR4PGD5 class"""

    @pytest.mark.parametrize(
        "input, error, expected",
        [
            ({"target_architecture": "PGD-Always-ON"}, None, True),
            ({"target_architecture": "other"}, None, False),
            ({}, AttributeError, False),
        ],
    )
    def test_bdr4pgd5_is_applicable(self, input, error, expected):
        """test is_applicable function"""
        x = BDR4PGD5()
        x._args = Namespace(**input)
        if error:
            with pytest.raises(error):
                assert x.is_applicable("cluster") == expected
        else:
            assert x.is_applicable("cluster") == expected

    def test_bdr4pgd5_check(
        self, basic_bdr_cluster, basic_pgd_cluster, basic_m1_cluster
    ):
        """test check function"""
        x = BDR4PGD5()
        assert len(x.check(basic_bdr_cluster).errors) == 0
        assert len(x.check(basic_bdr_cluster).warnings) == 0

        assert len(x.check(basic_m1_cluster).errors) == 1
        assert len(x.check(basic_m1_cluster).warnings) == 0

        assert len(x.check(basic_pgd_cluster).errors) == 1
        assert len(x.check(basic_bdr_cluster).warnings) == 0

        # add instances 'a' and 'b' with role 'bdr' in 'known' location
        basic_bdr_cluster.add_location("known")
        basic_bdr_cluster.add_instance("a", location_name="known")
        basic_bdr_cluster.instances.with_name("a").add_role("bdr")
        basic_bdr_cluster.add_instance("b", location_name="known")
        basic_bdr_cluster.instances.with_name("b").add_role("bdr")

        assert len(x.check(basic_bdr_cluster).errors) == 0
        assert len(x.check(basic_bdr_cluster).warnings) == 2

        # add instances 'c' and 'd' with role 'bdr' in 'reknown' location
        basic_bdr_cluster.add_location("reknown")
        basic_bdr_cluster.add_instance("c", location_name="reknown")
        basic_bdr_cluster.instances.with_name("c").add_role("bdr")
        basic_bdr_cluster.add_instance("d", location_name="reknown")
        basic_bdr_cluster.instances.with_name("d").add_role("bdr")

        assert len(x.check(basic_bdr_cluster).errors) == 1
        assert len(x.check(basic_bdr_cluster).warnings) == 4

    @pytest.mark.parametrize(
        "args, vars, error",
        [
            (
                {"target_architecture": "PGD-Always-ON", "pgd_proxy_routing": "local"},
                {"bdr_node_group": "basic", "bdr_version": "4"},
                None,
            ),
            (
                {"target_architecture": "PGD-Always-ON", "pgd_proxy_routing": "global"},
                {"bdr_node_group": "basic", "bdr_version": "4"},
                None,
            ),
            (
                {"target_architecture": "PGD-Always-ON", "pgd_proxy_routing": "global"},
                {
                    "bdr_node_group": "basic",
                    "bdr_version": "4",
                    "bdr_node_groups": "not_allowed",
                },
                "Can't reconfigure BDR4 clusters with bdr_node_groups defined",
            ),
            (
                {"target_architecture": "PGD-Always-ON", "pgd_proxy_routing": "global"},
                {
                    "bdr_node_group": "basic",
                    "bdr_version": "5",
                    "bdr_node_groups": "not_allowed",
                },
                "Don't know how to convert bdr_version from 5 to 5",
            ),
        ],
    )
    def test_bdr4pgd5_apply(self, args, vars, error, basic_bdr_cluster):
        """test apply function"""
        x = BDR4PGD5()
        x._args = Namespace(**args)

        basic_bdr_cluster.vars.update(vars)
        if error:
            with pytest.raises(ConfigureError) as e:
                x.apply(basic_bdr_cluster)
            assert e.value.args[0] == error
        else:
            x.apply(basic_bdr_cluster)

    def test_bdr4pgd5_description(self, basic_bdr_cluster):
        """test description function"""
        x = BDR4PGD5()
        camo_msg = "Define a commit scope to enable CAMO"
        assert camo_msg not in x.description(basic_bdr_cluster)._items

        basic_bdr_cluster.add_location("known")
        basic_bdr_cluster.add_instance(
            "a", location_name="known", host_vars={"bdr_node_camo_partner": "random"}
        )
        assert camo_msg in x.description(basic_bdr_cluster)._items

    def test_bdr4pgd5_is_ready_waits_for_repositories(self, basic_bdr_cluster):
        """is_ready returns False until its Repositories dep has been applied

        Because all_required() places a parent before its children, the
        framework's apply queue would otherwise run BDR4PGD5 before its own
        Repositories dependency. is_ready() must return False when the
        required Repositories hasn't been applied yet so the queue defers
        this transmogrifier until Repositories runs.
        """
        x = BDR4PGD5()
        # Fresh instance: Repositories exists in self.required but has no
        # _applied attribute yet, so is_ready must be False.
        assert x.is_ready(basic_bdr_cluster) is False

    def test_bdr4pgd5_is_ready_after_repositories_applied(self, basic_bdr_cluster):
        """is_ready returns True once every gating requirement is applied.

        The framework sets `_applied = True` on each transmogrifier after
        calling its apply(). Once that flag is present on the specialist's
        gating dependencies, is_ready must return True so the queue can
        finally apply BDR4PGD5.
        """
        x = BDR4PGD5()
        # Simulate the framework marking the requirement as applied.
        for req in x.required:
            req._applied = True
        assert x.is_ready(basic_bdr_cluster) is True

    def test_bdr4pgd5_is_ready_excludes_bdr_package_version(self, basic_bdr_cluster):
        """is_ready ignores BdrPackageVersion in its requires gate.

        BdrPackageVersion runs *after* BDR4PGD5 (it waits on cluster.
        architecture becoming PGD-Always-ON, which BDR4PGD5 does in its
        apply()). It's listed in our requires for inclusion in the run,
        not for ordering. If we waited for it to be _applied, the two
        transmogrifiers would deadlock waiting for each other.
        """
        x = BDR4PGD5()
        # Mark only Repositories applied; leave BdrPackageVersion unapplied.
        for req in x.required:
            if not isinstance(req, BdrPackageVersion):
                req._applied = True
        assert x.is_ready(basic_bdr_cluster) is True


class TestPGD5PGDX:
    """test suite for PGD5PGDX class"""

    @pytest.mark.parametrize(
        "input, expected",
        [
            ({"target_architecture": "PGD-X"}, True),
            ({"target_architecture": "PGD-Always-ON"}, False),
            ({"target_architecture": "other"}, False),
        ],
    )
    def test_pgd5pgdx_is_applicable(self, input, expected):
        """is_applicable returns True only when target_architecture is PGD-X

        PGD5PGDX handles the PGD-Always-ON → PGD-X migration. It must
        activate only for --architecture PGD-X so it doesn't interfere
        with other upgrade paths dispatched by Architecture.
        """
        x = PGD5PGDX()
        x._args = Namespace(**input)
        assert x.is_applicable("cluster") == expected

    def test_pgd5pgdx_is_ready_waits_for_repositories(self, basic_pgd_cluster):
        """is_ready returns False until its Repositories dep has been applied

        Same ordering constraint as BDR4PGD5: the framework's all_required()
        places the specialist before its Repositories, so is_ready() must
        defer PGD5PGDX until Repositories has run first.
        """
        x = PGD5PGDX()
        assert x.is_ready(basic_pgd_cluster) is False

    def test_pgd5pgdx_is_ready_after_repositories_applied(self, basic_pgd_cluster):
        """is_ready returns True once every gating requirement is applied.

        Once the framework marks the required Repositories with
        `_applied = True`, PGD5PGDX must signal ready so the queue can
        apply it.
        """
        x = PGD5PGDX()
        for req in x.required:
            req._applied = True
        assert x.is_ready(basic_pgd_cluster) is True


class TestCommon:
    """test suite for Common transmogrifier"""

    def test_common_check(self, basic_bdr_cluster):
        "test test check function"

        x = Common()
        assert len(x.check(basic_bdr_cluster).errors) == 0
        assert len(x.check(basic_bdr_cluster).warnings) == 0

    @pytest.mark.parametrize(
        "vars, expected",
        [
            ({"postgres_flavour": "postgresql"}, {"postgres_flavour": "postgresql"}),
            (
                {
                    "postgresql_flavour": "postgresql",
                },
                {"postgres_flavour": "postgresql"},
            ),
            ({"postgres_flavour": "2q"}, {"postgres_flavour": "pgextended"}),
            ({}, {}),
        ],
    )
    def test_common_apply(self, vars, expected, basic_bdr_cluster):
        "test test apply function"

        x = Common()
        basic_bdr_cluster.vars.update(vars)
        x.apply(basic_bdr_cluster)
        assert basic_bdr_cluster.vars == expected

    def test_common_description(self, basic_bdr_cluster):
        "test apply function"
        x = Common()
        assert x.description(basic_bdr_cluster)._items == ["No changes"]
        assert x.description(basic_bdr_cluster)._title is None


class TestRepositories:
    """test suite for Repositories transmogrifier"""

    def test_repositories_check(self, basic_bdr_cluster):
        "test test check function"

        x = Repositories()
        assert len(x.check(basic_bdr_cluster).errors) == 0
        assert len(x.check(basic_bdr_cluster).warnings) == 0

    @pytest.mark.parametrize(
        "vars, expected",
        [
            (
                {"postgres_flavour": "postgresql", "edb_repositories": []},
                {"postgres_flavour": "postgresql", "edb_repositories": ["standard"]},
            ),
            (
                {"postgres_flavour": "pgextended", "edb_repositories": []},
                {"postgres_flavour": "pgextended", "edb_repositories": ["standard"]},
            ),
            (
                {"postgres_flavour": "epas", "edb_repositories": []},
                {"postgres_flavour": "epas", "edb_repositories": ["enterprise"]},
            ),
            (
                {"postgres_flavour": "edbpge", "edb_repositories": []},
                {"postgres_flavour": "edbpge", "edb_repositories": ["standard"]},
            ),
        ],
    )
    def test_repositories_apply(self, vars, expected, basic_bdr_cluster):
        "test test apply function"

        x = Repositories()
        x._args = Namespace(edb_repositories=[])
        basic_bdr_cluster.vars.update(vars)
        x.apply(basic_bdr_cluster)
        assert basic_bdr_cluster.vars == expected

    def test_repositories_description(self, basic_bdr_cluster):
        "test apply function"
        x = Repositories()
        x._args = Namespace(edb_repositories=[])
        basic_bdr_cluster.vars.update(
            {"postgres_flavour": "postgresql", "edb_repositories": []}
        )
        assert x.description(basic_bdr_cluster)._items == [
            "Set edb_repositories to ['standard']"
        ]
        assert x.description(basic_bdr_cluster)._title is None


class TestBdrPackageVersion:
    """test suite for BdrPackageVersion transmogrifier"""

    def test_options(self):
        """--bdr-package-version is the option owned by this transmogrifier."""
        assert "--bdr-package-version" in BdrPackageVersion.options()

    @pytest.mark.parametrize(
        "version_string, expected",
        [
            ("*5.8*", True),
            ("*6.1.1*", True),
            ("5.5*", True),
            ("5.5.1", True),
            ("6.1.1", True),
            ("4:5.5.1", True),
            ("4:5.8.0", True),
            ("*5.3*", False),
            ("5.1.0", False),
            ("5.4.2", False),
            ("4:5.4.2", False),
        ],
    )
    def test_package_version_at_least(self, version_string, expected):
        """The lib/tpa-local copy of _package_version_at_least handles the
        same set of cases as the configure-side helper it mirrors."""
        assert (
            _package_version_at_least(version_string, BDR_WITH_READ_LISTEN_PORT)
            is expected
        )

    @pytest.mark.parametrize(
        "version_string",
        ["latest", "abc", "not-a-version", None, ""],
    )
    def test_package_version_at_least_malformed_raises(self, version_string):
        """Malformed version strings raise ConfigureError from tpa.exceptions
        (not ArchitectureError, which belongs to lib/tpaexec)."""
        with pytest.raises(ConfigureError):
            _package_version_at_least(version_string, BDR_WITH_READ_LISTEN_PORT)

    def test_is_applicable_always_true(self, basic_pgd_cluster):
        """is_applicable defaults to True. Selection upstream (options_match
        for standalone use, require() for the BDR4PGD5 path) is what
        determines whether we run at all."""
        x = BdrPackageVersion()
        x._args = Namespace(bdr_package_version=None, target_architecture=None)
        assert x.is_applicable(basic_pgd_cluster) is True

    @pytest.mark.parametrize(
        "architecture, target, expected",
        [
            # Standalone use on a supported architecture: ready
            # immediately.
            ("PGD-Always-ON", None, True),
            ("PGD-X", None, True),
            ("PGD-S", None, True),
            ("BDR-Always-ON", None, True),
            # Architecture-driven change in flight: wait for the
            # specialist to flip cluster.architecture to the target.
            ("BDR-Always-ON", "PGD-Always-ON", False),
            ("PGD-Always-ON", "PGD-X", False),
            # Once the flip has happened (cluster.architecture matches
            # target), we're ready.
            ("PGD-Always-ON", "PGD-Always-ON", True),
            ("PGD-X", "PGD-X", True),
            # Cluster shape we don't support and no target either:
            # never ready (caught by check()).
            ("M1", None, False),
        ],
    )
    def test_is_ready(self, architecture, target, expected):
        """is_ready is target-aware: when --architecture is being
        changed, wait for the flip; otherwise the cluster's current
        shape decides."""
        x = BdrPackageVersion()
        x._args = Namespace(bdr_package_version=None, target_architecture=target)
        cluster = Cluster("c", architecture, "docker")
        assert x.is_ready(cluster) is expected

    @pytest.mark.parametrize(
        "architecture, target, expected_errors",
        [
            # Standalone use on a supported architecture (incl.
            # BDR-Always-ON for BDR 3.x / 4.x minor upgrades).
            ("PGD-Always-ON", None, 0),
            ("PGD-X", None, 0),
            ("PGD-S", None, 0),
            ("BDR-Always-ON", None, 0),
            # Architecture-driven changes: the specialist will validate
            # whether the source→target transition is supported; we
            # accept any (source, supported-target) pair so we don't
            # block legitimate flows.
            ("BDR-Always-ON", "PGD-Always-ON", 0),
            ("PGD-Always-ON", "PGD-X", 0),
            # Cluster shape we don't support and no target either:
            # we'd deadlock at is_ready, so reject early.
            ("M1", None, 1),
        ],
    )
    def test_check_architecture(self, architecture, target, expected_errors):
        """check() permits the architectures we can run against and
        rejects those that would stall the apply queue."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.5.0",
            target_architecture=target,
        )
        cluster = Cluster("c", architecture, "docker")
        assert len(x.check(cluster).errors) == expected_errors

    def test_check_rejects_malformed_arg(self, basic_pgd_cluster):
        """A bad --bdr-package-version surfaces as a check() error so the
        user sees a clean message before apply runs."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="not-a-version",
            target_architecture=None,
        )
        result = x.check(basic_pgd_cluster)
        assert any("Cannot parse package version" in e for e in result.errors)

    def test_check_doesnt_validate_existing_cluster_vars_when_arg_given(
        self, basic_pgd_cluster
    ):
        """check() validates the user-supplied --bdr-package-version,
        but doesn't pre-validate a stale value already in cluster.vars
        — apply() will overwrite it with the (validated) arg anyway, so
        check() has nothing to flag."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.5.0",
            target_architecture=None,
        )
        basic_pgd_cluster.vars["bdr_package_version"] = "completely-bogus"
        assert len(x.check(basic_pgd_cluster).errors) == 0

    def test_description_propagates_bad_cluster_vars_version(self, basic_pgd_cluster):
        """If cluster.vars["bdr_package_version"] is unparseable and no
        --bdr-package-version arg was supplied to override it, a dry-run
        must surface that as an error rather than silently producing a
        description (epoch-prefix / wildcard syntax is easy to typo)."""
        x = BdrPackageVersion()
        x._args = Namespace(bdr_package_version=None, target_architecture=None)
        basic_pgd_cluster.vars["bdr_package_version"] = "not-a-version"
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        with pytest.raises(ConfigureError, match="Cannot parse package version"):
            x.description(basic_pgd_cluster)

    def test_apply_propagates_bad_cluster_vars_version(self, basic_pgd_cluster):
        """Apply mirrors description: no silent 'assume modern' fallback,
        so a malformed value that slipped past check() surfaces here."""
        x = BdrPackageVersion()
        x._args = Namespace(bdr_package_version=None, target_architecture=None)
        basic_pgd_cluster.vars["bdr_package_version"] = "not-a-version"
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        with pytest.raises(ConfigureError, match="Cannot parse package version"):
            x.apply(basic_pgd_cluster)

    def test_apply_records_version_arg(self, basic_pgd_cluster):
        """Supplying --bdr-package-version writes it into cluster.vars
        and then runs the version-gated rules."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.5.0",
            target_architecture=None,
        )
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        x.apply(basic_pgd_cluster)
        assert basic_pgd_cluster.vars["bdr_package_version"] == "5.5.0"
        assert (
            basic_pgd_cluster.vars["default_pgd_proxy_options"]["read_listen_port"]
            == DEFAULT_READ_LISTEN_PORT
        )

    def test_apply_skips_read_listen_port_for_old_version(self, basic_pgd_cluster):
        """Version < 5.5 → read_listen_port stays absent."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.4.2",
            target_architecture=None,
        )
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        x.apply(basic_pgd_cluster)
        assert basic_pgd_cluster.vars["default_pgd_proxy_options"] == {
            "listen_port": 6432,
        }

    def test_apply_no_version_assumes_latest(self, basic_pgd_cluster):
        """No --bdr-package-version arg, no existing cluster_vars setting:
        assume 'latest' and apply every rule. This is the no-arg BDR4PGD5
        path (where we're pulled in by require but the user didn't pass
        --bdr-package-version)."""
        x = BdrPackageVersion()
        x._args = Namespace(bdr_package_version=None, target_architecture=None)
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        x.apply(basic_pgd_cluster)
        assert (
            basic_pgd_cluster.vars["default_pgd_proxy_options"]["read_listen_port"]
            == DEFAULT_READ_LISTEN_PORT
        )

    def test_apply_no_proxy_options_is_noop(self, basic_pgd_cluster):
        """If default_pgd_proxy_options doesn't exist (e.g. no harp-proxy
        instances in the source cluster), the rule is silently skipped
        rather than synthesising the dict."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.5.0",
            target_architecture=None,
        )
        x.apply(basic_pgd_cluster)
        assert "default_pgd_proxy_options" not in basic_pgd_cluster.vars

    def test_apply_preserves_existing_read_listen_port(self, basic_pgd_cluster):
        """A read_listen_port already set in config.yml is not overwritten
        by the default — the user's chosen value wins."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.5.0",
            target_architecture=None,
        )
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {
            "listen_port": 6432,
            "read_listen_port": 7777,
        }
        x.apply(basic_pgd_cluster)
        assert (
            basic_pgd_cluster.vars["default_pgd_proxy_options"]["read_listen_port"]
            == 7777
        )

    def test_description_modern_version(self, basic_pgd_cluster):
        """description() lists the version assignment and the gated option."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.5.0",
            target_architecture=None,
        )
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        items = x.description(basic_pgd_cluster)._items
        assert any("bdr_package_version" in item for item in items)
        assert any("read_listen_port" in item for item in items)

    def test_description_old_version(self, basic_pgd_cluster):
        """description() omits the gated option when the version is too old."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.4.2",
            target_architecture=None,
        )
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        items = x.description(basic_pgd_cluster)._items
        assert not any("read_listen_port" in item for item in items)

    @pytest.mark.parametrize(
        "architecture",
        ["PGD-X", "PGD-S", "BDR-Always-ON"],
    )
    def test_description_omits_read_listen_port_on_non_pgd_proxy_arch(
        self, architecture
    ):
        """description() must not promise to add read_listen_port on
        clusters that don't (and won't) use pgd-proxy — connection-
        manager and harp-proxy clusters never gain the option."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.5.0",
            target_architecture=None,
        )
        cluster = Cluster("c", architecture, "docker")
        items = x.description(cluster)._items
        assert not any("read_listen_port" in item for item in items)

    def test_description_omits_read_listen_port_for_pgd_x_target(
        self, basic_pgd_cluster
    ):
        """When --architecture PGD-X is in flight, the cluster ends up on
        connection manager (PgdproxyCM removes default_pgd_proxy_options
        before PGD5PGDX runs), so description must not promise to add
        read_listen_port even when the source cluster is PGD-Always-ON."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="6.0.0",
            target_architecture="PGD-X",
        )
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        items = x.description(basic_pgd_cluster)._items
        assert not any("read_listen_port" in item for item in items)

    def test_description_omits_read_listen_port_when_cm_enabled(
        self, basic_pgd_cluster
    ):
        """A PGD-Always-ON cluster that has been migrated to connection
        manager (bdr.enable_builtin_connection_manager: true in
        postgres_conf_settings) is no longer a pgd-proxy cluster, even if
        it still has a default_pgd_proxy_options dict lingering in
        cluster_vars. The conf setting is the source of truth."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.9.0",
            target_architecture=None,
        )
        basic_pgd_cluster.vars["postgres_conf_settings"] = {
            "bdr.enable_builtin_connection_manager": "true",
        }
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        items = x.description(basic_pgd_cluster)._items
        assert not any("read_listen_port" in item for item in items)

    def test_apply_skips_read_listen_port_when_cm_enabled(self, basic_pgd_cluster):
        """And apply() agrees with description(): no read_listen_port
        added when CM is enabled on a PGD-Always-ON cluster."""
        x = BdrPackageVersion()
        x._args = Namespace(
            bdr_package_version="5.9.0",
            target_architecture=None,
        )
        basic_pgd_cluster.vars["postgres_conf_settings"] = {
            "bdr.enable_builtin_connection_manager": "true",
        }
        basic_pgd_cluster.vars["default_pgd_proxy_options"] = {"listen_port": 6432}
        x.apply(basic_pgd_cluster)
        assert basic_pgd_cluster.vars["default_pgd_proxy_options"] == {
            "listen_port": 6432,
        }


class TestBDR4PGD5ReadListenPort:
    """Integration: BDR4PGD5 + BdrPackageVersion produces a complete
    default_pgd_proxy_options entry on conversion to PGD-Always-ON."""

    def test_apply_queue_adds_both_ports(self, basic_bdr_cluster):
        """Running the full apply queue against a BDR-Always-ON cluster
        with a harp-proxy instance should produce a PGD-Always-ON config
        in which default_pgd_proxy_options has listen_port (set by
        BDR4PGD5) and read_listen_port (layered on by BdrPackageVersion)."""
        basic_bdr_cluster.add_location("known")
        basic_bdr_cluster.add_instance("hp", location_name="known")
        basic_bdr_cluster.instances.with_name("hp").add_role("harp-proxy")
        basic_bdr_cluster.add_instance("b", location_name="known")
        basic_bdr_cluster.instances.with_name("b").add_role("bdr")

        basic_bdr_cluster.vars.update(
            {
                "bdr_node_group": "basic",
                "bdr_version": "4",
                "postgres_flavour": "postgresql",
                "edb_repositories": [],
            }
        )

        tlist = transmogrifiers_from_args(
            ["--architecture", "PGD-Always-ON", "--pgd-proxy-routing", "local"]
        )
        apply_queue(basic_bdr_cluster, tlist)

        proxy_options = basic_bdr_cluster.vars["default_pgd_proxy_options"]
        assert proxy_options["listen_port"] == 6432
        assert proxy_options["read_listen_port"] == DEFAULT_READ_LISTEN_PORT
