#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""Tests for reconfigure command."""

import pytest
from tpa.commands.reconfigure import reconfigure, write_output
from tpa.cluster import Cluster
from tpa.exceptions import ConfigureError, PGDSDeprecatedError
import yaml
import os

CLUSTER_DIR = "lib/tests/config/basic-cluster"
PGDS_CLUSTER_DIR = "lib/tests/config/pgds-cluster"


@pytest.fixture
def create_cluster():
    cluster = Cluster(CLUSTER_DIR, "basic")
    if not os.path.exists(CLUSTER_DIR):
        os.mkdir(CLUSTER_DIR)
        with open(os.path.join(CLUSTER_DIR, "config.yml"), "w") as config:
            config.write(cluster.to_yaml())
    return cluster


@pytest.fixture
def create_pgds_cluster():
    # Simulates a config.yml hand-edited (or left over from before PGD-S
    # was blocked at configure time) to say architecture: PGD-S.
    cluster = Cluster(PGDS_CLUSTER_DIR, "PGD-S")
    if not os.path.exists(PGDS_CLUSTER_DIR):
        os.mkdir(PGDS_CLUSTER_DIR)
    with open(os.path.join(PGDS_CLUSTER_DIR, "config.yml"), "w") as config:
        config.write(cluster.to_yaml())
    return cluster


class TestReconfigure:
    """Test suite for reconfigure command"""

    @pytest.mark.parametrize(
        "input, expected, result",
        [
            (["--help"], pytest.raises(SystemExit), {"code": 0}),
            (
                ["lib/tests/config/invalid-cluster"],
                pytest.raises(ConfigureError),
                {"msg": "lib/tests/config/invalid-cluster/config.yml does not exist"},
            ),
            ([CLUSTER_DIR, "--describe"], None, {}),
            ([CLUSTER_DIR, "--check"], None, {}),
            (
                [
                    CLUSTER_DIR,
                ],
                pytest.raises(ConfigureError),
                {
                    "msg": "Nothing to do (add options to specify what to change; see --help)"
                },
            ),
        ],
    )
    def test_reconfigure_basic(self, input, expected, result, create_cluster):
        """test basic reconfigure function"""
        if expected:
            with expected as x:
                reconfigure(args=input)
            if "code" in result:
                assert x.value.code == result["code"]
            elif "msg" in result:
                assert x.value.args[0] == result["msg"]
        else:
            reconfigure(args=input)

    def test_reconfigure_rejects_pgds(self, create_pgds_cluster):
        """test that reconfigure rejects a config.yml specifying PGD-S"""
        with pytest.raises(PGDSDeprecatedError):
            reconfigure(args=[PGDS_CLUSTER_DIR, "--describe"])

    @pytest.mark.parametrize("mode", ["--describe", "--check"])
    def test_reconfigure_requires_pgd_proxy_routing(self, create_cluster, mode):
        """--pgd-proxy-routing is required for --architecture PGD-Always-ON

        This must be enforced up front, before dispatching to describe, check
        or apply, so that --describe can't silently skip it the way it would
        if this were left to the specialist's check() alone.
        """
        with pytest.raises(ConfigureError):
            reconfigure(args=[CLUSTER_DIR, "--architecture", "PGD-Always-ON", mode])

    def test_reconfigure_rejects_invalid_pgd_proxy_routing(self, create_cluster):
        """--pgd-proxy-routing only accepts 'global' or 'local'"""
        with pytest.raises(ConfigureError):
            reconfigure(
                args=[
                    CLUSTER_DIR,
                    "--architecture",
                    "PGD-Always-ON",
                    "--pgd-proxy-routing",
                    "bogus",
                    "--describe",
                ]
            )

    def test_reconfigure_pgd_x_unaffected_by_pgd_proxy_routing_requirement(
        self, create_cluster, capsys
    ):
        """--architecture PGD-X doesn't need --pgd-proxy-routing

        --pgd-proxy-routing is required only for the BDR4->PGD5
        (--architecture PGD-Always-ON) path. This confirms --architecture
        PGD-X still dispatches and runs its own checks without being blocked
        by that requirement, and that whatever it does report is its own
        business (unrelated to pgd-proxy-routing).
        """
        reconfigure(args=[CLUSTER_DIR, "--architecture", "PGD-X", "--check"])
        output = capsys.readouterr().out
        assert "pgd-proxy-routing" not in output

    def test_reconfigure_write_output(
        self,
        create_cluster,
        output="lib/tests/config/basic-cluster/output.yml",
    ):
        """test write_output function"""

        assert write_output(create_cluster, output) is None

        with open(output, "r") as result:
            assert yaml.safe_load(result) == {
                "architecture": "basic",
                "cluster_vars": {},
                "locations": [],
                "instance_defaults": {},
                "instances": [],
                "cluster_name": CLUSTER_DIR,
            }
