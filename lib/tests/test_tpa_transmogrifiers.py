#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""Tests for transmogrifier implementation object."""

from argparse import ArgumentParser, Namespace
import pytest

from tpa.cluster import Cluster
from tpa.exceptions import ConfigureError
from tpa.transmogrifiers import (
    BDR4PGD5,
    PGD5PGDX,
    Repositories,
    Replace2qRepositories,
    Common,
    Architecture,
    transmogrifiers_from_args,
    add_all_transmogrifier_options,
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
        """is_ready returns True once every required transmogrifier is applied

        The framework sets `_applied = True` on each transmogrifier after
        calling its apply(). Once that flag is present on the specialist's
        Repositories dependency, is_ready must return True so the queue
        can finally apply BDR4PGD5.
        """
        x = BDR4PGD5()
        # Simulate the framework marking the requirement as applied.
        for req in x.required:
            req._applied = True
        assert x.is_ready(basic_bdr_cluster) is True


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
