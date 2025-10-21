#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

"""Tests for transmogrifier implementation object."""

from argparse import ArgumentParser, Namespace
import pytest

from tpa.cluster import Cluster
from tpa.exceptions import ConfigureError
from tpa.transmogrifiers import (
    BDR4PGD5,
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
                [Common, Architecture, Repositories],
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
        self, tpa_2q_repositories, edb_repositories, extra_repositories, postgres_flavour, expected
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
            (cls.vars.get("edb_repositories") is None) or
            set(cls.vars.get("edb_repositories")) == set(expected)
        )

class TestArchitecture:
    """test suite for Architecture class"""

    def test_architecture_options(self):
        """test options function"""
        assert "--architecture" in Architecture.options()
        assert "--pgd-proxy-routing" in Architecture.options()

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
