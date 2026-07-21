#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""Tests for platform object."""

import pytest

from tpa.platform import Platform
from tpa.platforms.aws import aws as AwsPlatform


@pytest.fixture
def basic_platform():
    """generate a basic platform"""
    return Platform("test", "dummy")


class TestPlatform:
    """test suite for Platform class"""

    def test_platform_basic(self, basic_platform):
        """test basic Platform creation"""

        assert basic_platform.name == "test"


class TestAwsClusterVars:
    """update_cluster_vars on the aws platform opts the cluster in to
    sysctl_net via opt_in_tasks, so AWS clusters get TPA's busy-server
    network tuning without the user having to ask. Bare-metal stays
    opted-out. opt_in_tasks (not included_tasks) — populating
    included_tasks engages whitelist semantics and would gate every
    other task out of the deploy."""

    @pytest.fixture
    def aws_platform(self):
        return AwsPlatform("aws", arch=None)

    def test_adds_sysctl_net_when_opt_in_tasks_unset(self, aws_platform):
        cluster_vars = {}
        aws_platform.update_cluster_vars(cluster_vars, args={})
        assert cluster_vars["opt_in_tasks"] == ["sysctl_net"]

    def test_does_not_touch_included_tasks(self, aws_platform):
        cluster_vars = {}
        aws_platform.update_cluster_vars(cluster_vars, args={})
        assert "included_tasks" not in cluster_vars

    def test_preserves_existing_opt_in_tasks(self, aws_platform):
        cluster_vars = {"opt_in_tasks": ["something_else"]}
        aws_platform.update_cluster_vars(cluster_vars, args={})
        assert cluster_vars["opt_in_tasks"] == ["something_else", "sysctl_net"]

    def test_idempotent_when_already_opted_in(self, aws_platform):
        cluster_vars = {"opt_in_tasks": ["sysctl_net"]}
        aws_platform.update_cluster_vars(cluster_vars, args={})
        assert cluster_vars["opt_in_tasks"] == ["sysctl_net"]

    def test_handles_none_opt_in_tasks(self, aws_platform):
        cluster_vars = {"opt_in_tasks": None}
        aws_platform.update_cluster_vars(cluster_vars, args={})
        assert cluster_vars["opt_in_tasks"] == ["sysctl_net"]
