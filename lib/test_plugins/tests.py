#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

from jinja2 import Undefined

# This filter takes a container and a subkey ('x.y.z', or [x,y,z]) and returns
# true if the subkey exists in the container, or false if any of the levels is
# undefined.

def has_subkey(container, keys):
    try:
        v = container
        if isinstance(keys, basestring):
            keys = keys.split('.')
        for key in keys:
            v = v.get(key)
        return v and True or False
    except KeyError:
        return False

# Returns True if the given values are different, False otherwise.

def notequalto(a, b):
    return a != b

# Returns True if all of the one or more given values are in the container, and
# False otherwise.

def contains(container, *values):
    for v in values:
        if v not in container:
            return False
    return True

# Returns True if the given container is empty, False otherwise.

def empty(container):
    return len(container) == 0

class TestModule(object):
    def tests(self):
        return {
            'has_subkey': has_subkey,
            'notequalto': notequalto,
            'contains': contains,
            'empty': empty,
        }
