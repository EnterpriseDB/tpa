#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""Tests for the task_selector filter plugins."""

from filter_plugins.task_selector import (
    opts_in,
    permits,
    selects,
    strict_selects,
)


class TestPermits:
    """A tag is permitted unless it appears in the exclude list."""

    def test_unrestricted_is_permitted(self):
        assert permits({"exclude": []}, "anything") is True

    def test_excluded_is_not_permitted(self):
        assert permits({"exclude": ["foo"]}, "foo") is False

    def test_unrelated_exclude_still_permits(self):
        assert permits({"exclude": ["foo"]}, "bar") is True


class TestSelects:
    """selects matches permits when the include list is empty;
    once include is non-empty, only tags in it pass (whitelist
    semantics)."""

    def test_default_on_when_include_empty(self):
        assert selects({"include": [], "exclude": []}, "anything") is True

    def test_explicitly_included(self):
        assert selects({"include": ["foo"], "exclude": []}, "foo") is True

    def test_whitelist_excludes_others(self):
        assert selects({"include": ["foo"], "exclude": []}, "bar") is False

    def test_exclude_wins_over_include(self):
        assert selects({"include": ["foo"], "exclude": ["foo"]}, "foo") is False


class TestStrictSelects:
    """strict_selects is opt-in only: a tag is on if and only if it
    appears in the include list."""

    def test_default_off(self):
        assert strict_selects({"include": [], "exclude": []}, "anything") is False

    def test_explicitly_included(self):
        assert strict_selects({"include": ["foo"], "exclude": []}, "foo") is True

    def test_not_in_include_is_off(self):
        assert strict_selects({"include": ["foo"], "exclude": []}, "bar") is False

    def test_exclude_wins_over_include(self):
        assert strict_selects({"include": ["foo"], "exclude": ["foo"]}, "foo") is False


class TestOptsIn:
    """opts_in is opt-in only, like strict_selects, but uses its own
    list — orthogonal to include — so a task can be opted in without
    engaging the whitelist semantics that gate every other task out."""

    def test_default_off(self):
        assert opts_in({"opt_in": [], "exclude": []}, "anything") is False

    def test_explicitly_opted_in(self):
        assert opts_in({"opt_in": ["foo"], "exclude": []}, "foo") is True

    def test_not_in_opt_in_is_off(self):
        assert opts_in({"opt_in": ["foo"], "exclude": []}, "bar") is False

    def test_exclude_wins_over_opt_in(self):
        assert opts_in({"opt_in": ["foo"], "exclude": ["foo"]}, "foo") is False

    def test_include_does_not_opt_in(self):
        # Putting a tag in include should not enable an opts_in() gate.
        assert opts_in({"include": ["foo"], "opt_in": [], "exclude": []}, "foo") is False

    def test_orthogonal_to_include_whitelist(self):
        # The key design property: populating opt_in does not engage
        # selects() whitelist semantics on unrelated tags.
        selector = {"include": [], "opt_in": ["foo"], "exclude": []}
        assert selects(selector, "bar") is True
