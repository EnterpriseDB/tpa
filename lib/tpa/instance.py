#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

from typing import Any
from collections import ChainMap

from .exceptions import InstanceError


class Instance:
    """This class represents a server to deploy to."""

    def __init__(
        self,
        name: str,
        cluster,
        location_name,
        settings=None,
        host_vars=None,
    ):
        self._name: str = name
        self._cluster = cluster
        if cluster.get_location_by_name(location_name) is not None:
            self._location = cluster.get_location_by_name(location_name)
        else:
            raise InstanceError(f"Could not find location '{location_name}'.")
        self._settings = settings or {}
        self._host_vars = host_vars or {}

    def __repr__(self):
        return f"Instance({self.name!r})"

    @property
    def name(self):
        """The name of this instance"""
        return self._name

    @property
    def roles(self):
        """A list of roles set anywhere in the cluster for this instance"""
        return self.get_setting("role", [])

    @property
    def location(self):
        """The location that this instance belongs to"""
        return self._location

    @property
    def settings(self):
        """This instance's settings

        These are the settings specified directly for this instance, not
        anything inherited through its location or instance_defaults."""

        return self._settings

    @property
    def host_vars(self):
        """This instance's inventory variables

        These are the inventory variables specified directly for this instance,
        not including anything inherited through group membership."""

        return self._host_vars

    def effective_vars(self):
        """Generate a ChainMap with the various vars applied to the instance
        ordered the same way ansible inventory would be applied.
        Returns:
            ChainMap : all vars applicable to the instance
        """
        return ChainMap(
            self.host_vars,
            self._cluster.instance_defaults.get("vars", {}),
            self.location.group.group_vars or {},
            self._cluster.group.group_vars,
        )

    def get_hostvar(self, key, default=None):
        """Returns the value of the given key or the given default value if the
        key is not in the instance's host_vars, its location's group_vars, or
        the cluster's main group's group_vars (i.e., cluster_vars)."""

        v = self.effective_vars()
        return v.get(key, default)

    def get_setting(self, key, default=None) -> Any:
        """Returns the value of the given key or the given default value if the
        key is not in the instance's settings, the cluster's instance_defaults,
        or the instance's location's settings."""

        v = ChainMap(
            self.settings, self._cluster.instance_defaults, self.location.settings or {}
        )
        return v.get(key, default)

    def add_role(self, r):
        """Adds the given role to this instance's roles"""
        self._settings.setdefault("role", []).append(r)

    def to_yaml_dict(self):
        d = {
            "Name": self.name,
            "location": self.location.name or "",
            **self.settings,
        }
        if self.host_vars:
            d.update({"vars": self.host_vars})
        return d
