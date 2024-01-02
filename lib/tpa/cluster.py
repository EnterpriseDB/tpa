#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

from typing import List, Dict, Any, Optional
import yaml
import copy

from .exceptions import ClusterError
from .group import Group
from .location import Location
from .instance import Instance
from .instances import Instances


class Cluster:
    """A cluster is a named collection of locations, groups, instances, and an
    assortment of key-value settings (apart from the key-value settings attached
    to the locations, groups, and instances). It's an object representation that
    corresponds exactly to a config.yml file.

    A cluster comprises instances in one or more locations (read: data centres),
    and contains information used to construct an Ansible inventory (instances,
    groups, and associated variables) as well as information needed to provision
    cluster resources (which may or may not be platform-specific, and some of
    which may also be copied into the inventory).

    A cluster has a main inventory group (corresponding to cluster_vars) and one
    subgroup per location. Every instance belongs to the group for the location
    it is in, and inherits membership in the main group thereby."""

    def __init__(self, cluster_name, architecture, platform=None, group_vars=None):
        self._name: str = cluster_name
        self._original_yaml: Optional[Dict[str, Any]] = None
        self._architecture: str = architecture
        self._platform: Optional[str] = platform
        self._group = Group(cluster_name, group_vars=group_vars)
        self._locations: List[Location] = []
        self._instances: List[Instance] = []
        self._instance_defaults = {}
        self._settings = {}

    @property
    def name(self):
        """The name of this cluster"""
        return self._name

    @property
    def architecture(self):
        """The architecture that this cluster was initialised with"""
        return self._architecture

    @property
    def platform(self):
        """The platform that this cluster was initialised with (may be None if
        the platform is not known)"""
        return self._platform

    @property
    def group(self):
        """The main inventory group for this cluster

        The cluster_vars in config.yml are the group_vars set for this group."""

        return self._group

    @property
    def vars(self):
        """The vars for the main inventory group for this cluster, corresponding
        to cluster_vars."""

        return self._group.group_vars

    @property
    def locations(self):
        """A list of locations in this cluster"""
        return self._locations

    @property
    def instances(self):
        """A list of instances in this cluster"""
        return Instances(self._instances)

    @property
    def instance_defaults(self):
        """Default settings for all instances in this cluster"""
        return self._instance_defaults

    @property
    def settings(self):
        """Settings for this cluster, other than cluster_vars, locations,
        instance_defaults, and instances"""
        return self._settings

    def get_location_by_name(self, location_name):
        """Returns the location with the given location_name, or None if it is
        not defined for this cluster."""

        return next((loc for loc in self.locations if loc.name == location_name), None)

    def add_location(self, location_name: str, **kwargs) -> Location:
        """Creates a location with the given name, add it to this cluster along
        with its associated group, and return the new location"""

        loc = Location(location_name, **kwargs)
        self._group.add_subgroup(loc.group)
        self._locations.append(loc)
        return loc

    def add_instance(self, instance_name: str, **kwargs):
        """Creates an instance with the given name, add it to this cluster, and
        return the new instance"""
        if instance_name not in self.instances.get_names():
            i = Instance(instance_name, cluster=self, **kwargs)
            self._instances.append(i)
            return i
        else:
            raise ClusterError(
                f"A node with the name: {instance_name} already exists in the cluster"
            )

    def to_yaml(self):
        """Returns a YAML representation of this cluster (WIP)

        There are four major top-level sections: a dict named cluster_vars, a
        list of locations, a dict of instance_defaults, and a list of instances.
        Then there are some other settings, depending on platform etc."""

        c = {"architecture": self.architecture, **self.settings}
        c.update(
            {
                "cluster_vars": self.group.group_vars,
                "locations": [loc.to_yaml_dict() for loc in self.locations],
                "instance_defaults": self.instance_defaults,
                "instances": [i.to_yaml_dict() for i in self.instances],
            }
        )

        # XXX Quick prototype to reproduce original YAML document key order (but
        # not comments, which we can't do with pyyaml anyway). Needs testing.

        def _reorder_keys(d: Dict[str, Any], ref: Dict[str, Any]) -> Dict[str, Any]:
            """Returns the contents of d while preserving the key order of
            ref as far as possible."""
            result = {}
            for key, val in ref.items():
                if key not in d:
                    continue
                if isinstance(val, dict) and isinstance(d[key], dict):
                    result[key] = _reorder_keys(d[key], val)
                    del d[key]
                else:
                    result[key] = d[key]
                    del d[key]
            result.update(d)
            return result

        if self._original_yaml:
            c = _reorder_keys(c, self._original_yaml)
        return yaml.safe_dump(c, sort_keys=False)

    @staticmethod
    def from_yaml(config_filename, cluster_name=None):
        """Returns a new Cluster object initialised from the contents of the
        given config.yml file"""

        y = {}
        with open(config_filename) as doc:
            y = yaml.safe_load(doc)
            original_yaml = copy.deepcopy(y)

        if not cluster_name:
            cluster_name = "unknown"

        c = Cluster(
            cluster_name,
            y.pop("architecture", "unknown"),
            group_vars=y.pop("cluster_vars", {}),
        )
        c._original_yaml = original_yaml

        locations = y.pop("locations", [])
        for loc in locations:
            c.add_location(
                loc.pop("Name"), group_vars=loc.pop("vars", {}), settings=loc
            )

        c._instance_defaults = y.pop("instance_defaults", {})

        instances = y.pop("instances", [])
        for i in instances:
            c.add_instance(
                i.pop("Name"),
                location_name=i.pop("location"),
                host_vars=i.pop("vars", {}),
                settings=i,
            )

        c.settings.update(y)

        return c
