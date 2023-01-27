#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

"""Tests for architecture object."""

import pytest

from tpa.architecture import Architecture
from tpa.architectures import M1, BDRAlwaysON, PGDAlwaysON


class BasicArchitecture(Architecture):
    """Basic Architecure class to test common functions inherited from Architecture class"""
    pass


@pytest.fixture
def basic_architecture():
    """generate a basic architecture"""

    return Architecture()


class TestArchitecture:
    """test suite for Architecture class"""

    def test_architecture_basic(self, basic_architecture):
        """test basic Architecture creation"""

        pass


@pytest.fixture
def basic_m1():
    """generate a basic M1 architecture"""

    pass


class TestM1:
    """test suite for M1 Architecture class"""

    def test_m1_basic(self, basic_m1):
        """test basic M1 Architecture creation"""

        pass


@pytest.fixture
def basic_bdrao():
    """generate a basic BDRAlwaysON architecture"""

    pass


class TestBDRAO:
    """test suite for BDRAlwaysON Architecture class"""

    def test_bdrao_basic(self, basic_bdrao):
        """test basic BDRAlwaysON Architecture creation"""

        pass


@pytest.fixture
def basic_pgdao():
    """generate a basic PGDAlwaysON architecture"""

    pass


class TestPGDAO:
    """test suite for PGDAlwaysON Architecture class"""

    def test_pgdao_basic(self, basic_pgdao):
        """test basic PGDAlwaysON Architecture creation"""

        pass
