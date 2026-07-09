#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""
Tests for tpa_warning() and the tpa callback's recap of deliberate warnings.

These run in a single process, so os.getpid() matches the controller pid the
callback records at wrap time -- which is the path that actually records.
"""

import pytest
from ansible.utils.display import Display

from ..tpa_warnings import tpa_warning, WARNING_MARKER
from ..callback_plugins.tpa import CallbackModule
from ..filter_plugins.instances import normalize_roles


@pytest.fixture
def wrapped_display():
    """A Display singleton with the tpa callback's warning wrapper installed
    and an empty collection list."""

    CallbackModule()  # installs the wrapper on the Display singleton (idempotent)
    display = Display()
    display._tpa_deliberate_warnings = []
    return display


def test_tpa_warning_is_recorded_with_marker_stripped(wrapped_display):
    tpa_warning("a deliberate warning")

    assert wrapped_display._tpa_deliberate_warnings == ["a deliberate warning"]
    # The marker is an implementation detail and must never reach what we store
    # (nor, therefore, what the recap displays).
    assert all(
        WARNING_MARKER not in w for w in wrapped_display._tpa_deliberate_warnings
    )


def test_plain_warning_is_not_recorded(wrapped_display):
    # Warnings Ansible itself raises (no marker) must not enter the recap list.
    wrapped_display.warning("a benign ansible warning")

    assert wrapped_display._tpa_deliberate_warnings == []


def test_empty_role_warning_reaches_the_recap(wrapped_display):
    # The empty-role warning from TPA-1526 is raised via tpa_warning(), so it
    # must land in the recap list rather than only printing inline.
    normalize_roles(["primary", None], "node1")

    assert any(
        "empty role entry" in w for w in wrapped_display._tpa_deliberate_warnings
    )


def test_duplicate_deliberate_warnings_are_deduplicated(wrapped_display):
    tpa_warning("same message")
    tpa_warning("same message")

    assert wrapped_display._tpa_deliberate_warnings == ["same message"]
