#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

"""Tests for transmogrifier object."""

import pytest
from argparse import Namespace
from unittest.mock import PropertyMock, patch

from tpa.checkresult import CheckResult
from tpa.changedescription import ChangeDescription
from tpa.cluster import Cluster

from tpa.transmogrifier import Transmogrifier, opt, apply, check, describe
from tpa.exceptions import ConfigureError, TransmogrifierError


class BasicTransmogrifier(Transmogrifier):
    """Basic transmogrifier class to test common functions"""

    def __init__(self, _requires=None):
        self._requires = _requires or []

    def apply(self, cluster: Cluster):
        return super().apply(cluster)

    def description(self, cluster: Cluster) -> ChangeDescription:
        super().description(cluster)
        return ChangeDescription(items=["one change", "another change"])

    def check(self, cluster: Cluster) -> list:
        super().check(cluster)
        return CheckResult()


@pytest.fixture
def basic_transmogrifier():
    """generate a basic Transmogrifier"""
    return BasicTransmogrifier()


@pytest.fixture
def basic_cluster():
    return Cluster("cluster", "arch", "platform")


# mocked function for various tests
def errors():
    return ["this is an error"]


def is_ready(self, cluster):
    return False


def is_applicable(self, cluster):
    return False


class TestTransmogrifier:
    """test suite for Transmogrifier class"""

    def test_transmogrifier_basic(self, basic_transmogrifier):
        """test basic Transmogrifier creation"""

        assert basic_transmogrifier.options() == {}
        assert basic_transmogrifier.args == Namespace()
        assert basic_transmogrifier.required == []

    @pytest.mark.parametrize(
        "requires",
        [
            [],
            [BasicTransmogrifier()],
            [BasicTransmogrifier(), BasicTransmogrifier()],
        ],
    )
    def test_transmogrifier_set_parsed_args(self, basic_transmogrifier, requires):
        """test set_parsed_args function"""

        basic_transmogrifier._requires = requires
        assert basic_transmogrifier.set_parsed_args(Namespace()) is None

    @pytest.mark.parametrize(
        "requires",
        [
            None,
            BasicTransmogrifier(),
        ],
    )
    def test_transmogrifier_require(self, basic_transmogrifier, requires):
        """test require function"""

        basic_transmogrifier.require(requires)
        assert requires in basic_transmogrifier.required

    @pytest.mark.parametrize(
        "requires",
        [BasicTransmogrifier(), BasicTransmogrifier(_requires=[BasicTransmogrifier()])],
    )
    def test_transmogrifier_all_required(self, basic_transmogrifier, requires):
        """test all_required function"""

        basic_transmogrifier.require(requires)
        assert requires in basic_transmogrifier.all_required()

    def test_transmogrifier_is_applicable(self, basic_transmogrifier, basic_cluster):
        """test is_applicable function"""

        assert basic_transmogrifier.is_applicable(basic_cluster) is True

    def test_transmogrifier_is_ready(self, basic_transmogrifier, basic_cluster):
        """test is_ready function"""

        assert basic_transmogrifier.is_ready(basic_cluster) is True

    def test_transmogrifier_description(self, basic_transmogrifier, basic_cluster):
        """test description function"""

        assert basic_transmogrifier.description(basic_cluster)._items == [
            "one change",
            "another change",
        ]

    def test_transmogrifier_check(self, basic_transmogrifier, basic_cluster):
        """test check function"""

        assert type(basic_transmogrifier.check(basic_cluster)) == CheckResult

    def test_transmogrifier_apply(self, basic_transmogrifier, basic_cluster):
        """test apply function"""

        assert basic_transmogrifier.apply(basic_cluster) is None

    @pytest.mark.parametrize(
        "args, kwargs, expected",
        [
            (
                ["--platform", "-p"],
                {"default": "aws"},
                {"--platform": {"aliases": ("-p",), "default": "aws"}},
            ),
            (
                ["--test"],
                {"default": "test"},
                {"--test": {"default": "test"}},
            ),
            (
                ["--platform", "-p", "-P"],
                {"default": "aws"},
                {"--platform": {"aliases": ("-p", "-P"), "default": "aws"}},
            ),
            (
                ["--platform"],
                {},
                {"--platform": {}},
            ),
        ],
    )
    def test_transmogrifier_opt(self, args, kwargs, expected):
        """test opt helper function"""

        assert opt(*args, **kwargs) == expected

    @pytest.mark.parametrize(
        "tlist",
        [
            [],
            [BasicTransmogrifier()],
        ],
    )
    def test_transmogrifier_apply(self, tlist, basic_cluster):
        """test apply helper function"""

        if tlist:
            assert apply(basic_cluster, tlist) is None
        else:
            with pytest.raises(ConfigureError):
                assert apply(basic_cluster, tlist) is None

    def test_transmogrifier_apply_errors(
        self, basic_cluster, tlist=[BasicTransmogrifier()]
    ):
        """test apply helper function error case L.152"""

        with patch.object(CheckResult, "errors", new_callable=PropertyMock) as mock:
            mock.return_value = errors()
            with pytest.raises(TransmogrifierError):
                assert apply(basic_cluster, tlist)

    @patch.object(BasicTransmogrifier, "is_ready", is_ready)
    def test_transmogrifier_apply_not_ready(
        self, basic_cluster, tlist=[BasicTransmogrifier()]
    ):
        """test apply helper function error case L.174"""

        with pytest.raises(TransmogrifierError):
            assert apply(basic_cluster, tlist)

    def test_transmogrifier_describe(
        self, basic_cluster, tlist=[BasicTransmogrifier()]
    ):
        """test describe helper function"""

        assert str(describe(basic_cluster, tlist)) == "* one change\n* another change"
        tlist[0].require(BasicTransmogrifier())
        assert (
            str(describe(basic_cluster, tlist))
            == "* one change\n* another change\n* one change\n* another change"
        )

    @patch.object(BasicTransmogrifier, "is_applicable", is_applicable)
    def test_transmogrifier_describe_fail(
        self, basic_cluster, tlist=[BasicTransmogrifier()]
    ):
        """test describe helper function with no applicable Transmogrifier"""

        assert str(describe(basic_cluster, tlist)) == "* No changes"

    def test_transmogrifier_check(self, basic_cluster, tlist=[BasicTransmogrifier()]):
        """test describe helper function with no applicable Transmogrifier"""

        assert type(check(basic_cluster, tlist)) == CheckResult

    @patch.object(BasicTransmogrifier, "is_applicable", is_applicable)
    def test_transmogrifier_check_fail(
        self, basic_cluster, tlist=[BasicTransmogrifier()]
    ):
        """test describe helper function with no applicable Transmogrifier"""

        assert type(check(basic_cluster, tlist)) == CheckResult
