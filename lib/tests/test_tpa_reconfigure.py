#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

"""Tests for reconfigure command."""

import pytest
from tpa.commands.reconfigure import reconfigure, write_output
from tpa.cluster import Cluster
from tpa.exceptions import ConfigureError
import yaml
import os

CLUSTER_DIR="lib/tests/config/basic-cluster"
@pytest.fixture
def create_cluster():
    cluster = Cluster(CLUSTER_DIR,"basic")
    if not os.path.exists(CLUSTER_DIR):
        os.mkdir(CLUSTER_DIR)
        with open(os.path.join(CLUSTER_DIR,"config.yml"),"w") as config:
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
            }
