#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

"""Tests for platform object."""

import pytest

from tpa.platform import Platform


@pytest.fixture
def basic_platform():
    """generate a basic platform"""
    return Platform("test", "dummy")


class TestPlatform:
    """test suite for Platform class"""

    def test_platform_basic(self, basic_platform):
        """test basic Platform creation"""

        assert basic_platform.name == "test"
