#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.


from typing import List, Optional

from tpa.exceptions import ConfigureError
from tpa.instance import Instance


class Instances(list):
    """Represents a collection of instances, and provides methods to operate on
    all or a selected subset of those instances."""

    def __init__(self, *args):
        super().__init__(*args)

    def select(self, callback):
        """Returns a new collection of instances for which the given callback
        returns true."""
        return Instances([i for i in self if callback(i)])

    def with_name(self, name: str):
        """Returns a new collection of instances that have the given name. Use
        .only() to retrieve the instance itself, or .maybe() if you're not sure
        that there is one.
        """
        return Instances([i for i in self if i.name == name])

    def with_role(self, role: str):
        """Returns a new collection of instances that have the given role."""
        return Instances([i for i in self if role in i.roles])

    def with_roles(self, roles: List[str]):
        """Returns a new collection of instances that have all of the given
        list of role names."""
        return Instances([i for i in self if set(roles).issubset(i.roles)])

    def without_role(self, role: str):
        """Returns a new collection of instances that don't have the given role."""
        return Instances([i for i in self if role not in i.roles])

    def without_roles(self, roles: List[str]):
        """Returns a new collection of instances that have none of the given
        list of role names."""
        return Instances([i for i in self if set(roles).isdisjoint(i.roles)])

    def in_location(self, location_name):
        """Returns a new collection of instances in the given location."""
        return Instances([i for i in self if i.location.name == location_name])

    def with_hostvar(self, key, **kwargs):
        """Returns a new collection of instances that have the given key set
        under host_vars (directly on the instance), or set to a particular
        value, if specified in kwargs."""

        val = kwargs.get("value")
        return Instances(
            [
                i
                for i in self
                if key in i.host_vars and (val is None or i.host_vars.get(key) == val)
            ]
        )

    def with_bdr_node_kind(self, kind: str):
        """Returns a new collection of instances with the given BDR node kind
        (witness, subscriber-only, standby, or data).
        """

        # XXX This duplicates bdr_node_kind in lib/filter_plugins/bdr.py as a
        # temporary helper function for convenience.
        def bdr_node_kind(role: List[str]) -> str:
            if "bdr" in role:
                if "witness" in role:
                    return "witness"
                elif "subscriber-only" in role:
                    return "subscriber-only"
                elif "standby" in role:
                    return "standby"
                else:
                    return "data"
            else:
                return ""

        return Instances([i for i in self if bdr_node_kind(i.roles) == kind])

    def get_names(self):
        ret = []
        for i in self:
            ret.append(i.name)
        return ret

    def add_role(self, role):
        """Adds the given role to the instances in this list."""
        for i in self:
            i.add_role(role)
        return self

    def set_hostvar(self, var, val):
        """Sets the given var=val on the instances in this list."""
        for i in self:
            i.host_vars[var] = val
        return self

    def only(self) -> Instance:
        """Returns a single Instance if it is the only one in the collection, or
        raises an error because you must have been expecting the collection to
        contain only one instance if you used this method in the first place.
        """
        num = len(self)
        if num == 1:
            return self[0]
        raise ConfigureError(
            f"Internal error: expected .only() one instance, found {num}"
        )

    def maybe(self) -> Optional[Instance]:
        """Returns a single Instance if it is the only one in the collection, or
        None if the collection is empty, or raises an error because you expected
        the collection to contain at most one instance if you used this method.
        """
        num = len(self)
        if num > 1:
            raise ConfigureError(
                f"Internal error: expected at most one instance, found {num}"
            )
        elif num == 1:
            return self[0]
        return None
