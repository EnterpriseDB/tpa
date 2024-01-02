#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

from .group import Group
import re


class Location:
    """A location represents a level of redundancy in server hosting, defined in
    whatever way makes sense for a particular cluster (AWS regions, availability
    zones, actual data centres, and so on). It is associated with an inventory
    group (i.e., if you have a location named x, the inventory will contain a
    group named location_x), and both have key-value settings attached.

    Every instance in a cluster must belong to exactly one location. From this
    location each instance inherits the attached key-value settings."""

    def __init__(
        self,
        location_name: str,
        group_vars=None,
        settings=None,
        witness_only: bool = False,
    ):
        self._name: str = location_name
        self._group: Group = Group(f"location_{location_name}", group_vars=group_vars)
        self._settings = settings or {}
        self._witness_only = witness_only

    def __repr__(self):
        return f"Location({self.name!r})"

    @property
    def name(self):
        """The name of this location"""
        return self._name

    @property
    def group(self):
        """The group associated with this location"""
        return self._group

    @property
    def settings(self):
        """The settings for this location"""
        return self._settings

    @property
    def witness_only(self):
        """The location is witness only"""
        return self._witness_only

    @property
    def sub_group_name(self):
        """
        Returns a name for the BDR subgroup in the given location.
        based on location name sanitized.
        """
        sub = re.sub("[^a-z0-9_]", "_", self.name.lower())
        return f"{sub}_subgroup"

    def to_yaml_dict(self):
        d = {
            "Name": self.name,
            **self.settings,
        }
        if self.group.group_vars:
            d.update({"vars": self.group.group_vars})
        return d
