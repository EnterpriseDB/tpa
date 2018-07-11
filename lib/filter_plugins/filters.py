#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
from jinja2 import Undefined
from jinja2.runtime import StrictUndefined
from ansible.errors import AnsibleFilterError

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

# Given a list of hostnames and the names of a primary instance and some other
# instance (and a copy of hostvars), returns the name of an instance that has
# «backup: xxx» defined and is descended from the primary. It will prefer the
# first backed-up instance in the same region as "somehost", otherwise return
# the first backed-up instance. Returns None if no instances match.

def instance_with_backup_of(hosts, primary, somehost, hostvars):
    candidates = []

    for h in hosts:
        if hostvars[h].get('backup', '') != '' and \
            upstream_root(h, hostvars) == primary:
            candidates.append(h)

    for backedup in candidates:
        if hostvars[backedup].get('region', 'left') == \
            hostvars[somehost].get('region', 'right'):
            return c
    if candidates:
        return candidates[0]

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
            vars = v.get('vars', {})
            results.append(dict(device=dev, **vars))
    return results

# Takes a dict and a list of keys and returns a new dict which has none of the
# keys in the list.

def remove_keys(d, keys):
    if not isinstance(d, dict):
        raise AnsibleFilterError("|remove_keys takes a dict as its first argument, got " + repr(d))

    if not isinstance(keys, list):
        raise AnsibleFilterError("|remove_keys takes a list as its second argument, got " + repr(keys))

    d2 = copy.deepcopy(d)
    for k in keys:
        if k in d2:
            del d2[k]

    return d2

# Takes a conninfo string and returns a dict of the settings it represents, or
# if given a key, returns the value if the key is specified, or None.

def parse_conninfo(conninfo, key=None):

    settings = {}
    for str in conninfo.split(' '):
        parts = [x.strip() for x in str.strip().split('=', 1)]

        v = None
        if len(parts) == 2:
            v = parts[1]
            if v.startswith("'") and v.endswith("'") or \
               v.startswith('"') and v.endswith('"'):
                v = v[1:-1]

        settings[parts[0]] = v

    if key:
        return settings.get(key, None)

    return settings

# Takes the name of an image and returns a string corresponding to
# ansible_distribution values.

def identify_os(name):
    name = name.lower()

    if 'rhel' in name or 'redhat' in name:
        return 'RedHat'
    elif 'debian' in name:
        return 'Debian'
    elif 'ubuntu' in name:
        return 'Ubuntu'

    return 'Unknown'

# Given a hash that maps os names to package lists, the name of an os, and an
# optional version suffix, this function returns a list of packages for the
# given os, with the version suffix applied (if provided).

def packages_for(packages, os, version):
    ret = []

    for p in packages[os]:
        if not isinstance(version, StrictUndefined):
            sep = '='
            if os == 'RedHat':
                sep = '-'
            p = '%s%s%s' % (p, sep, version)
        ret.append(p)

    return ret

class FilterModule(object):
    def filters(self):
        return {
            'try_subkey': try_subkey,
            'doublequote': doublequote,
            'upstream_root': upstream_root,
            'instance_with_backup_of': instance_with_backup_of,
            'get_device_variables': get_device_variables,
            'remove_keys': remove_keys,
            'parse_conninfo': parse_conninfo,
            'identify_os': identify_os,
            'packages_for': packages_for,
        }
