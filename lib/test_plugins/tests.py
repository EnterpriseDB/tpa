#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

from ansible.plugins.test.core import match

# This filter takes a container and a subkey ('x.y.z', or [x,y,z]) and returns
# true if the subkey exists in the container, or false if any of the levels is
# undefined.


def has_subkey(container, keys):
    try:
        v = container
        if isinstance(keys, str):
            keys = keys.split(".")
        for key in keys:
            v = v.get(key)
        return v and True or False
    except KeyError:
        return False


# Returns True if the given values are different, False otherwise.


def notequalto(a, b):
    return a != b


def contains(container, *values):
    """
    Returns True if all of the one or more given values are in the container,
    and False otherwise.
    """
    for v in values:
        if v not in container:
            return False
    return True


def contains_any(container, *values):
    """
    Returns True if any of the one or more given values are in the container,
    and False otherwise.
    """
    for v in values:
        if v in container:
            return True
    return False


# Returns True if the given str starts with the given prefix, False otherwise.


def startswith(str, prefix):
    return str.startswith(prefix)


# Returns True if the given container is empty, False otherwise.


def empty(container):
    return len(container) == 0


class TestModule(object):
    def tests(self):
        return {
            "has_subkey": has_subkey,
            "notequalto": notequalto,
            "contains": contains,
            "contains_all": contains,
            "contains_any": contains_any,
            "startswith": startswith,
            "empty": empty,
            "matched_by": match,
        }
