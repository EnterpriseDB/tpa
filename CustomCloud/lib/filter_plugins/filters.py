#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
from jinja2 import Undefined
from jinja2.runtime import StrictUndefined

# Based on PR ansible/ansible#11083, this filter takes a container and a subkey
# ('x.y.z', or [x,y,z]) and a default value, and returns container.x.y.z or the
# default value if any of the levels is undefined.

def try_subkey(container, keys, default=None):
    try:
        v = container
        if isinstance(keys, basestring):
            keys = keys.split('.')
        for key in keys:
            v = v.get(key, default)
        if isinstance(v, StrictUndefined):
            v = default
        return v
    except:
        return default

# Given 'foo', returns '"foo"'. Blindly converts each embedded double quote in
# the string to '\"'. Caveat emptor.

def doublequote(str):
    return '"%s"' % str.replace('"', '\"')

# Given a hostname and hostvars, returns the name of the earliest ancestor that
# doesn't have an upstream defined.

def upstream_root(h, hostvars):
    while h in hostvars and hostvars[h].get('upstream', '') != '':
        h = hostvars[h].get('upstream')
    return h

# Given a list of hostnames and a primary name and hostvars, returns the name of
# the first listed instance that is descended from the primary and has a backup
# instance defined, or None if none of the given named instances meets those
# criteria.

def instance_with_backup_of(hosts, primary, hostvars):
    for h in hosts:
        if hostvars[h].get('backup', '') != '' and \
            upstream_root(h, hostvars) == primary:
            return h
    return None

# Takes a list of volumes and returns a new list where there is only one entry
# per device name (raid_device if defined, else device_name), consisting of the
# device name and any variables defined for it.

def get_device_variables(volumes):
    seen = set()
    results = []
    for v in volumes:
        dev = v.get('raid_device', v.get('device_name'))
        if dev not in seen:
            seen.add(dev)
            results.append(dict(device=dev, vars=v.get('vars', [])))
    return results

class FilterModule(object):
    def filters(self):
        return {
            'try_subkey': try_subkey,
            'doublequote': doublequote,
            'upstream_root': upstream_root,
            'instance_with_backup_of': instance_with_backup_of,
            'get_device_variables': get_device_variables,
        }
