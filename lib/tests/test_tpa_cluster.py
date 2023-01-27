#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

"""Tests for cluster object."""

import pytest

from tpa.exceptions import ConfigureError, ClusterError
from tpa.cluster import Cluster
from tpa.architectures import PGDAlwaysON, BDRAlwaysON


class TestCluster:
    """Cluster test suite"""

    # basic Cluster generation
    @pytest.fixture
    def basic_bdr_cluster(self):
        basic = Cluster("basic", "BDR-Always-ON", "bare")
        basic.add_location("first")
        basic.add_instance(
            "data_node",
            location_name="first",
            host_vars={},
            settings={"role": ["bdr"]},
        )
        basic.add_instance(
            "proxy_node",
            location_name="first",
            host_vars={},
            settings={"role": ["harp-proxy"]},
        )
        return basic

    def test_cluster_basic(self, basic_bdr_cluster):
        """test basic cluster creation"""

        assert basic_bdr_cluster.name == "basic"
        assert basic_bdr_cluster.architecture == "BDR-Always-ON"
        assert basic_bdr_cluster.platform == "bare"
        assert basic_bdr_cluster.group.name == "basic"
        assert basic_bdr_cluster.vars == {}
        assert basic_bdr_cluster.instance_defaults == {}
        assert basic_bdr_cluster.settings == {}

    def test_cluster_instance(self, basic_bdr_cluster):
        """test instance functionalities of a cluster"""

        assert len(basic_bdr_cluster.instances) == 2

        basic_bdr_cluster.add_instance("new_node", location_name="first")
        assert len(basic_bdr_cluster.instances) == 3

        with pytest.raises(ClusterError):
            assert basic_bdr_cluster.add_instance("new_node", location_name="first")

    def test_cluster_location(self, basic_bdr_cluster):
        """test location functionalities of a cluster"""
        assert len(basic_bdr_cluster.locations) == 1

        basic_bdr_cluster.add_location("second")
        assert len(basic_bdr_cluster.locations) == 2

    def test_cluster_get_location(self, basic_bdr_cluster):
        """test get_location_by_name function"""
        assert basic_bdr_cluster.get_location_by_name("first") is not None
        assert basic_bdr_cluster.get_location_by_name("second") is None

    def test_cluster_yaml(self, basic_bdr_cluster):
        """test yaml functionalities of a cluster"""
        output_file = "lib/tests/config/to_yaml.yml"
        with open(output_file, "w") as f:
            f.write(basic_bdr_cluster.to_yaml())

        from_yaml = Cluster.from_yaml(output_file)

        # verify clusters match
        assert len(basic_bdr_cluster.locations) == len(from_yaml.locations)
        assert len(basic_bdr_cluster.instances) == len(from_yaml.instances)
        assert basic_bdr_cluster.instances.get_names() == from_yaml.instances.get_names()

        # test covering _reorder_keys() function
        assert from_yaml.to_yaml()
