#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.


class Group:
    """A group is a named container for key-value settings. It corresponds to an
    Ansible inventory group."""

    def __init__(
        self,
        name: str,
        group_vars=None,
        subgroups=None,
    ):
        self._name: str = name
        self._group_vars = group_vars or {}
        self._subgroups: list[Group] = subgroups or []

    def __repr__(self):
        fields = [f"{self.name!r}"]

        if self.group_vars:
            fields += [f"group_vars={self.group_vars!r}"]

        if self.subgroups:
            fields += [f"subgroups={self.subgroups!r}"]

        return f"Group({', '.join(fields)})"

    @property
    def name(self):
        """The name of this group"""
        return self._name

    @property
    def subgroups(self):
        """The children of this group"""
        return self._subgroups

    @property
    def group_vars(self):
        """The inventory vars for this group"""
        return self._group_vars

    def add_subgroup(self, g):
        """Adds the group object g as a child of this group"""
        self._subgroups.append(g)

    def add_to_group_vars(self, new_vars: dict):
        """Adds the supplied vars, overwriting existing ones if
           there are conflicts"""
        for k,v in new_vars.items():
            self._group_vars[k] = v

    def remove_from_group_vars(self, vars: list):
        """Removes the vars with the supplied keys from the group"""
        """Given a list of variable names, removes those variables from
           the group"""
        for k in vars:
            self._groups_vars.pop(k, None)
