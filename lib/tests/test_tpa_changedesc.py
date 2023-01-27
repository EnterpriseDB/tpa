#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

import pytest

from tpa.changedescription import ChangeDescription


@pytest.fixture
def basic_changedesc():
    return ChangeDescription(title="Test", items=["Change 1", "Change 2"])


class TestChangeDesc:

    def test_changedesc_basic(self, basic_changedesc):
        """test basic ChangeDescription creation"""

        assert basic_changedesc._title == "Test"
        assert basic_changedesc._items == ["Change 1", "Change 2"]

    def test_changedesc_str(self, basic_changedesc):
        """test __str__ function"""

        basic_changedesc._items.append(ChangeDescription(title="subtest", items=["subchange 1"]))
        assert str(basic_changedesc) == '* Test\n  * Change 1\n  * Change 2\n  * subtest\n    * subchange 1'