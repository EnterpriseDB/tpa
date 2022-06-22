#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.
"""Testing net module."""
import os.path
from ipaddress import IPv4Network

import pytest

from tpaexec.net import Network, Subnets
from tpaexec.architecture import Architecture
from tpaexec.exceptions import NetError


@pytest.fixture()
def network():
    yield Network(cidr="10.0.0.0/16", size=8)


class TestNetwork:
    def test_network_overlaps(self, network):
        assert network.overlaps(IPv4Network("10.0.0.0/8"))


@pytest.fixture
def subnets():
    yield Subnets(cidr="10.0.0.0/24")


@pytest.fixture
def subnet_too_large():
    yield Subnets(cidr="10.0.0.0/8", new_prefix=9)


@pytest.fixture
def subnet_too_small():
    yield Subnets(cidr="10.0.0.0/29", new_prefix=30)


class TestSubnets:
    def test_subnets_slice(self, subnets):
        assert [str(s) for s in subnets.slice(1)] == ["10.0.0.0/28"]

    def test_subnets_exclude(self, subnets):
        subnets.exclude(["10.0.0.0/28"])
        assert [str(s) for s in subnets.slice(1)] == ["10.0.0.16/28"]

    def test_subnets_exclude_multi(self, subnets):
        subnets.exclude(["10.0.0.0/28", "10.0.0.16/28"])
        assert [str(s) for s in subnets.slice(1)] == ["10.0.0.32/28"]

    def test_subnets_empty_exclude(self, subnets):
        subnets.exclude([])
        assert [str(s) for s in subnets.slice(1)] == ["10.0.0.0/28"]

    def test_subnets_shuffle(self, subnets):
        sub_list = subnets.ranges[:]
        subnets.shuffle()
        assert set(subnets.ranges) == set(sub_list)
        assert not subnets.ranges == sub_list

    def test_subnets_too_large(self, subnet_too_large):
        with pytest.raises(NetError) as exc:
            subnet_too_large.validate()
        assert exc.value.args == ('prefix length for subnets must be between 23-29: 9',)

    def test_subnets_too_small(self, subnet_too_small):
        with pytest.raises(NetError) as exc:
            subnet_too_small.validate()
        assert exc.value.args == ('prefix length for subnets must be between 23-29: 30',)

    def test_subnets_get(self, subnets):
        assert subnets[0] == IPv4Network("10.0.0.0/28")


class TestArchitectureSubnet:
    def test_exclusion_files(self):
        base = os.path.join(os.path.dirname(__file__), "net_fixtures", "cluster_config")
        dirs = [os.path.join(base, "cluster1"), os.path.join(base, "cluster2")]
        subnets = Architecture._get_subnets_from(exclude_dirs=dirs)
        subnets.sort()
        assert subnets == [
            "10.33.1.0/28",
            "10.33.19.0/28",
            "10.33.190.32/28",
            "10.33.202.240/28",
            "10.33.237.96/28",
            "10.33.74.160/28",
        ]
