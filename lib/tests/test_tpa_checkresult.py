#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

"""Tests for checkresult object."""

from tpa.checkresult import CheckResult


class TestCheckResult:
    """Test suite for CheckResult class"""

    WARNING = "A warning"
    ERROR = "An error"

    def test_checkresult_basic(self):
        """test basic checkresult creation"""
        cr = CheckResult()
        assert cr.warnings == []
        assert cr.errors == []

    def test_checkresult_error(self):
        """test error function"""
        cr = CheckResult()
        assert cr.errors == []
        cr.error(self.ERROR)
        assert cr.errors == [self.ERROR]

    def test_checkresult_warning(self):
        """test warning function"""
        cr = CheckResult()
        assert cr.warnings == []
        cr.warning(self.WARNING)
        assert cr.warnings == [self.WARNING]

    def test_checkresult_absorb(self):
        """test absorb function"""
        cr = CheckResult()
        cr2 = CheckResult()

        cr2.warning(self.WARNING)
        cr2.error(self.ERROR)
        cr.absorb(cr2)
        assert cr.errors == [self.ERROR]
        assert cr.warnings == [self.WARNING]

    def test_checkresult_str(self):
        """test __str__ function"""

        cr = CheckResult()
        cr.warning(self.WARNING)
        cr.error(self.ERROR)

        print(cr)
        assert str(cr) == "Warnings:\n* A warning\nErrors:\n* An error"
