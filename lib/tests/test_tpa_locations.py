#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

"""Tests for location object."""
import pytest

from tpa.location import Location

@pytest.fixture
def basic_location():
    """generatet a basic location"""
    return Location("test")


class TestLocation:
    """test suite for location class"""

    def test_location_basic(self, basic_location):
        """test basic location creation"""

        assert basic_location.name == "test"
        assert basic_location.group.name == "location_test"
        assert basic_location.group.group_vars == {}
        assert basic_location.settings == {}
        assert basic_location.witness_only == False
        assert basic_location.sub_group_name == "test_subgroup"

    def test_location_to_yaml_dict(self, basic_location):
        """test to_yaml_dict function"""

        assert basic_location.to_yaml_dict()
        basic_location.group._group_vars = {"test": "test"}
        assert basic_location.to_yaml_dict()

    def test_location_repr(self, basic_location):
        """test __repr__ function"""

        assert str(basic_location) == "Location('test')"
