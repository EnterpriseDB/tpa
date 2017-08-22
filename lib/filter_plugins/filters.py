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

# Takes a dict and a list of keys and returns a new dict which has none of the
# keys in the list.

def remove_keys(d, keys):
    if not isinstance(d, dict):
        raise errors.AnsibleFilterError("|remove_keys takes a dict as its first argument, got " + repr(d))

    if not isinstance(keys, list):
        raise errors.AnsibleFilterError("|remove_keys takes a list as its second argument, got " + repr(keys))

    d2 = copy.deepcopy(d)
    for k in keys:
        if k in d2:
            del d2[k]

    return d2

class FilterModule(object):
    def filters(self):
        return {
            'try_subkey': try_subkey,
            'doublequote': doublequote,
            'upstream_root': upstream_root,
            'instance_with_backup_of': instance_with_backup_of,
            'get_device_variables': get_device_variables,
            'remove_keys': remove_keys,
        }
