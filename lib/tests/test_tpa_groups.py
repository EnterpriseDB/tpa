#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

"""Tests for group object."""

import pytest

from tpa.group import Group


@pytest.fixture
def basic_group():
    """generate a basic group"""
    return Group("test")


class TestGroup:
    """test suite for Group class"""

    def test_group_basic(self, basic_group):
        """test basic Group creation"""

        assert basic_group.name == "test"
        assert basic_group.group_vars == {}
        assert basic_group.subgroups == []

    def test_group_repr(self, basic_group):
        """test __repr__ function"""

        assert str(basic_group) == "Group('test')"
        basic_group._subgroups = [Group("subtest")]
        basic_group._group_vars = {"test": "test"}
        assert (
            str(basic_group)
            == "Group('test', group_vars={'test': 'test'}, subgroups=[Group('subtest')])"
        )

    def test_group_add_subgroup(self, basic_group):
        """test add_subgroup function"""

        assert basic_group.subgroups == []
        assert basic_group.add_subgroup(Group("subtest")) is None
        assert basic_group.subgroups[0].name == "subtest"
