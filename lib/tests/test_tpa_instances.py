#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

"""Tests for instance object."""
import pytest

from tpa.cluster import Cluster
from tpa.instances import Instances
from tpa.instance import Instance
from tpa.exceptions import InstanceError, ConfigureError


@pytest.fixture
def basic_cluster():
    """generate a basic cluster"""
    cluster = Cluster("cluster", "basic")
    cluster.add_location("known")
    return cluster


@pytest.fixture
def basic_instance(basic_cluster, location_name):
    """generate a basic instance"""
    try:
        instance = Instance("basic", basic_cluster, location_name=location_name)
    except Exception as e:
        return e
    return instance


class TestInstance:
    """Test for instance functionalities"""

    @pytest.mark.parametrize("location_name", ["unknown", "known"])
    def test_instance_basic(self, location_name, basic_instance):
        """Basic instance creation verification"""

        if location_name == "known":
            assert basic_instance.name == "basic"
            assert basic_instance.location.name == "known"
            assert basic_instance.settings == { 'node': 1 }
            assert basic_instance.roles == []
            assert basic_instance.host_vars == {}
        else:
            assert type(basic_instance) == InstanceError

    @pytest.mark.parametrize("location_name", ["known"])
    def test_instance_get_hostvar(self, basic_instance):
        """test get_hostvars function"""

        assert basic_instance.get_hostvar("test") is None
        assert basic_instance.get_hostvar("test", []) == []

        basic_instance._host_vars = {"test": ["list"]}
        assert basic_instance.get_hostvar("test") == ["list"]

    @pytest.mark.parametrize("location_name", ["known"])
    def test_instance_add_role(self, basic_instance):
        """test add_role function"""

        assert basic_instance.roles == []
        assert basic_instance.add_role("test") is None
        assert basic_instance.roles == ["test"]

    @pytest.mark.parametrize("location_name", ["known"])
    def test_instance_to_yaml_dict(self, basic_instance):
        """test to_yaml function"""

        assert basic_instance.to_yaml_dict()

        basic_instance._host_vars = {"test": ["test"]}
        assert basic_instance.to_yaml_dict()

    @pytest.mark.parametrize("location_name", ["known"])
    def test_instance_repr(self, basic_instance):
        """test __repr__ function"""
        assert str(basic_instance) == "Instance('basic')"


@pytest.fixture
def basic_instances(basic_cluster):
    """create a basic instances"""
    basic_cluster.add_instance("a", location_name="known")
    basic_cluster.add_instance("b", location_name="known")

    instances = Instances(basic_cluster.instances)
    return instances


@pytest.fixture
def instances_with_roles(basic_instances):
    """generate instances with roles"""

    for instance in basic_instances:
        if instance.name == "a":
            instance.add_role("bdr")
            instance.add_role("witness")
        else:
            instance.add_role("bdr")
            instance.add_role("pgd-proxy")
            instance.add_role("barman")
    return basic_instances


@pytest.fixture
def instances_with_hostvars(basic_instances):
    """generate instances with roles"""
    for instance in basic_instances:
        if instance.name == "a":
            instance._host_vars = {"test": "test"}

        else:
            instance._host_vars = {
                "t_list": ["one", "two", "three"],
                "t_bool": True,
                "t_int": 10,
                "t_dict": {"a": "b"},
            }
    return basic_instances


@pytest.fixture
def instances_with_kind(basic_cluster):
    """generate instances with roles  for each node_kind"""
    basic_cluster.add_instance(
        "w", location_name="known", settings={"role": ["witness", "bdr"]}
    )
    basic_cluster.add_instance(
        "s", location_name="known", settings={"role": ["standby", "bdr"]}
    )
    basic_cluster.add_instance(
        "so", location_name="known", settings={"role": ["subscriber-only", "bdr"]}
    )
    basic_cluster.add_instance(
        "data", location_name="known", settings={"role": ["bdr"]}
    )
    basic_cluster.add_instance(
        "other", location_name="known", settings={"role": ["barman"]}
    )
    return Instances(basic_cluster.instances)


class TestInstances:
    """test Instances class"""

    def test_instances_basic(self, basic_instances):
        """test basic instances functions"""

        assert basic_instances.get_names() == ["a", "b"]

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("a", ["a"]),
            ("b", ["b"]),
            ("c", []),
        ],
    )
    def test_instances_select(self, instances_with_roles, input, expected):
        """test select function"""

        def callback(i):
            return True if i.name == input else False

        assert instances_with_roles.select(callback).get_names() == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("bdr", ["a", "b"]),
            ("unknown", []),
            (1, []),
        ],
    )
    def test_instances_with_role(self, instances_with_roles, input, expected):
        """test with_role function"""

        assert instances_with_roles.with_role(input).get_names() == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("a", ["a"]),
            ("c", []),
            (1, []),
        ],
    )
    def test_instances_with_name(self, basic_instances, input, expected):
        """test with_name function"""

        assert basic_instances.with_name(input).get_names() == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("data", ["data"]),
            ("other", []),
            ("witness", ["w"]),
            ("standby", ["s"]),
            ("subscriber-only", ["so"]),
        ],
    )
    def test_instances_with_bdr_node_kind(self, instances_with_kind, input, expected):
        """test with_bdr_node_kind function"""

        assert instances_with_kind.with_bdr_node_kind(input).get_names() == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            (["bdr"], ["a", "b"]),
            (["unknown"], []),
            (["bdr", "pgd-proxy"], ["b"]),
            (["bdr", "pgd-proxy", "witness"], []),
        ],
    )
    def test_instances_with_roles(self, instances_with_roles, input, expected):
        """test with_roles function"""
        assert instances_with_roles.with_roles(input).get_names() == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("bdr", []),
            ("unknown", ["a", "b"]),
            (1, ["a", "b"]),
        ],
    )
    def test_instances_without_role(self, instances_with_roles, input, expected):
        """test without_role function"""

        assert instances_with_roles.without_role(input).get_names() == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            (["bdr"], []),
            (["unknown"], ["a", "b"]),
            (["bdr", "pgd-proxy"], []),
        ],
    )
    def test_instances_without_roles(self, instances_with_roles, input, expected):
        """test without_roles function"""
        assert instances_with_roles.without_roles(input).get_names() == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("known", ["a", "b"]),
            ("unknown", []),
        ],
    )
    def test_instances_in_location(self, instances_with_roles, input, expected):
        """test in_location function"""
        assert instances_with_roles.in_location(input).get_names() == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            ({"key": "test"}, ["a"]),
            ({"key": "unknown"}, []),
            ({"key": "t_list"}, ["b"]),
            ({"key": "t_bool"}, ["b"]),
            ({"key": "t_dict"}, ["b"]),
            ({"key": "t_bool", "value": True}, ["b"]),
        ],
    )
    def test_instances_with_hostvar(self, instances_with_hostvars, input, expected):
        """test with_hostvar function"""

        assert instances_with_hostvars.with_hostvar(**input).get_names() == expected

    @pytest.mark.parametrize(
        "input",
        [
            "test_role",
            None,
        ],
    )
    def test_instances_add_role(self, basic_instances, input):
        """test add_role function"""

        assert basic_instances.with_role(input).get_names() == []
        assert basic_instances.add_role(input)
        assert basic_instances.with_role(input).get_names() == ["a", "b"]

    def test_instances_only(self, basic_cluster, basic_instances):
        """test only function"""
        instances = Instances()
        with pytest.raises(ConfigureError):
            assert instances.only()
            assert basic_instances.only()
        instances = Instances(
            [Instance("a", cluster=basic_cluster, location_name="known")]
        )
        assert instances.only().name == "a"

    def test_instances_maybe(self, basic_cluster, basic_instances):
        """test maybe function"""
        instances = Instances()
        assert instances.maybe() is None
        with pytest.raises(ConfigureError):
            assert basic_instances.maybe()
        instances = Instances(
            [Instance("a", cluster=basic_cluster, location_name="known")]
        )
        assert instances.maybe().name == "a"
