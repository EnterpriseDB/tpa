#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

import copy
from jinja2 import Undefined
from jinja2.runtime import StrictUndefined
from ansible.errors import AnsibleFilterError

# This table is distilled from the content at
# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html#instance-store-volumes
# https://aws.amazon.com/ec2/instance-types/

ephemeral_storage = {
    'c1.medium': 1, # 350 GB† HDD
    'c1.xlarge': 4, # 420 GB (1.6 TB) HDD
    'c3.large': 2, # 16 GB (32 GB) SSD
    'c3.xlarge': 2, # 40 GB (80 GB) SSD
    'c3.2xlarge': 2, # 80 GB (160 GB) SSD
    'c3.4xlarge': 2, # 160 GB (320 GB) SSD
    'c3.8xlarge': 2, # 320 GB (640 GB) SSD
    'cc2.8xlarge': 4, # 840 GB (3.36 TB) HDD
    'cr1.8xlarge': 2, # 120 GB (240 GB) SSD
    'd2.xlarge': 3, # 2,000 GB (6 TB) HDD
    'd2.2xlarge': 6, # 2,000 GB (12 TB) HDD
    'd2.4xlarge': 12, # 2,000 GB (24 TB) HDD
    'd2.8xlarge': 24, # 2,000 GB (48 TB) HDD
    'g2.2xlarge': 1, # 60 GB SSD
    'g2.8xlarge': 2, # 120 GB (240 GB) SSD
    'h1.2xlarge': 1, # 2000 GB (2 TB) HDD
    'h1.4xlarge': 2, # 2000 GB (4 TB) HDD
    'h1.8xlarge': 4, # 2000 GB (8 TB) HDD
    'h1.16xlarge': 8, # 2000 GB (16 TB) HDD
    'hs1.8xlarge': 24, # 2,000 GB (48 TB) HDD
    'i2.xlarge': 1, # 800 GB SSD
    'i2.2xlarge': 2, # 800 GB (1.6 TB) SSD
    'i2.4xlarge': 4, # 800 GB (3.2 TB) SSD
    'i2.8xlarge': 8, # 800 GB (6.4 TB) SSD
    'm1.small': 1, # 160 GB† HDD
    'm1.medium': 1, # 410 GB HDD
    'm1.large': 2, # 420 GB (840 GB) HDD
    'm1.xlarge': 4, # 420 GB (1.6 TB) HDD
    'm2.xlarge': 1, # 420 GB HDD
    'm2.2xlarge': 1, # 850 GB HDD
    'm2.4xlarge': 2, # 840 GB (1.68 TB) HDD
    'm3.medium': 1, # 4 GB SSD
    'm3.large': 1, # 32 GB SSD
    'm3.xlarge': 2, # 40 GB (80 GB) SSD
    'm3.2xlarge': 2, # 80 GB (160 GB) SSD
    'r3.large': 1, # 32 GB SSD
    'r3.xlarge': 1, # 80 GB SSD
    'r3.2xlarge': 1, # 160 GB SSD
    'r3.4xlarge': 1, # 320 GB SSD
    'r3.8xlarge': 2, # 320 GB (640 GB) SSD
    'x1.16xlarge': 1, # 1,920 GB SSD
    'x1.32xlarge': 2, # 1,920 GB (3.84 TB) SSD
    'x1e.xlarge': 1, # 120 GB SSD
    'x1e.2xlarge': 1, # 240 GB SSD
    'x1e.4xlarge': 1, # 480 GB SSD
    'x1e.8xlarge': 1, # 960 GB SSD
    'x1e.16xlarge': 1, # 1,920 GB SSD
    'x1e.32xlarge': 2, # 1,920 GB (3.84 TB) SSD
}

## Instance filters
#
# The filters defined here take the array of instances (from config.yml)
# and other inputs and return a new array of instances with parameters
# suitably adjusted.

# Returns a hash of the IP addresses specified for a given instance.

def ip_addresses(instance):
    addresses = {}

    for a in ['ip_address', 'public_ip', 'private_ip']:
        ip = instance.get(a)
        if ip is not None:
            addresses[a] = ip

    addresses['ip_address'] = instance.get('ip_address', instance.get('public_ip', instance.get('private_ip')))

    return addresses

# Every instance must have certain settings (e.g., tags) in a specific format.

def set_instance_defaults(old_instances, cluster_name, instance_defaults, locations):
    instances = []

    locations_map = {}
    for l in locations:
        locations_map[l['Name']] = l

    # Returns a mapping with the keys in defaults (excluding those given in
    # omit_keys) and the corresponding values from item (if specified) or from
    # defaults otherwise. Any dict values are further merged for convenience, so
    # that defaults can specify some keys and item can override or extend them.

    def merged_defaults(item, defaults, omit_keys=[]):
        result = {}

        for key in [k for k in defaults if k not in omit_keys]:
            result[key] = item.get(key, defaults[key])
            if isinstance(result[key], dict) and isinstance(defaults[key], dict):
                b = copy.deepcopy(defaults[key])
                b.update(result[key])
                result[key] = b

        return result

    for i in old_instances:
        j = copy.deepcopy(i)
        tags = j.get('tags', {})

        # Every instance must have a sensible name (lowercase, without
        # underscores). If it's set under .tags, we'll move it up.

        name = j.get('Name', tags.get('Name', None))
        if name is None:
            name = cluster_name +'-'+ str(j['node'])
        j['Name'] = name.replace('_', '-').lower()
        j['vars'] = j.get('vars', {})

        # Anything set in instance_defaults should be copied to the instance,
        # unless the instance has a setting that overrides the default. As a
        # convenience, we also merge dict keys (so that once can, for example,
        # set some vars in instance_defaults and some on the instance, and get
        # all of them, with the instance settings overriding the defaults).

        j.update(merged_defaults(j, instance_defaults, omit_keys=['default_volumes']))

        # If instance_defaults specifies 'default_volumes', we merge those
        # entries with the instance's 'volumes', with entries in the latter
        # taking precedence over default entries with the same device name.
        # (Setting 'volumes' to [] explicitly in instances will remove the
        # defaults altogether.)

        volumes = j.get('volumes', [])
        default_volumes = instance_defaults.get('default_volumes', [])
        if default_volumes and (len(volumes) > 0 or 'volumes' not in j):
            volume_map = {}
            for vol in default_volumes + volumes:
                name = vol.get('raid_device', vol.get('device_name'))
                if name.startswith('/dev/'):
                    name = name[5:]
                volume_map[name] = vol

            volumes = []
            for name in sorted(volume_map.keys()):
                volumes.append(volume_map[name])

            j['volumes'] = volumes

        # If the instance specifies «location: x», where x is either a name or
        # an array index (for backwards compatibility), we copy the settings
        # from location x to the instance, in exactly the same way as we do
        # above for instance_defaults.

        location = j.get('location', None)
        if len(locations) > 0 and location is not None:
            if isinstance(location, int) and location < len(locations):
                location = locations[location]
            elif location in locations_map:
                location = locations_map[location]
            else:
                raise AnsibleFilterError("Instance %s specifies unknown location %s" % (j['Name'], location))

            j.update(merged_defaults(j, location, omit_keys=['Name']))

        # The upstream, backup, and role tags should be moved one level up if
        # they're specified at all.

        for t in ['upstream', 'backup', 'role']:
            if t in tags:
                j[t] = tags[t]
                del tags[t]

        # The role tag should be a list, so we convert comma-separated
        # strings if that's what we're given.

        role = j.get('role', [])
        if not isinstance(role, list):
            role = map(lambda x: x.strip(), role.split(","))

        # primary/replica instances must also be tagged 'postgres'.

        if 'primary' in role or 'replica' in role:
            if 'postgres' not in role:
                role = role + ['postgres']

        j['role'] = role
        j['tags'] = tags

        # Name and node should be in tags, but we'll add them in when we're
        # actually creating the tags, not before.

        for t in ['name', 'Name', 'node']:
            if t in tags:
                del tags[t]

        instances.append(j)

    return instances

# This filter sets the image for each instance, if not already specified.

def expand_instance_image(old_instances, ec2_region_amis):
    instances = []

    for i in old_instances:
        j = copy.deepcopy(i)

        if 'image' not in j:
            j['image'] = ec2_region_amis[j['region']]

        instances.append(j)

    return instances

# This filter translates a device name of 'root' to the given root
# device name, and sets delete_on_termination to true if it's not
# implied by attach_existing or explicitly set to be false.

def expand_instance_volumes(old_instances, ec2_ami_properties):
    instances = []

    for i in old_instances:
        j = copy.deepcopy(i)

        volumes = []
        for vol in j.get('volumes', []):
            v = copy.deepcopy(vol)
            vars = v.get('vars', {})

            if v['volume_type'] == 'none':
                continue

            if v['device_name'] == 'root':
                v['device_name'] = ec2_ami_properties[j['image']]['root_device_name']
                if 'mountpoint' in vars or 'volume_for' in vars:
                    raise AnsibleFilterError("root volume cannot have mountpoint/volume_for set")
            if not 'delete_on_termination' in v:
                v['delete_on_termination'] = not v.get('attach_existing',False)

            volume_for = vars.get('volume_for', None)
            if volume_for and \
                volume_for not in ['postgres_data', 'barman_data']:
                raise AnsibleFilterError("volume_for=%s is not recognised for volume %s" % (volume_for, v['device_name']))

            volumes.append(v)

            # If the entry specifies raid_device, then we repeat this volume
            # raid_units-1 times.

            if 'raid_device' in v:
                n = v['raid_units']

                if n == 'all':
                    if 'ephemeral' in v:
                        if i['type'] in ephemeral_storage:
                            n = ephemeral_storage[i['type']]
                        else:
                            raise AnsibleFilterError("ephemeral storage unavailable for %s" % i['type'])
                    else:
                        raise AnsibleFilterError("raid_units=all can be used only with ephemeral storage")
                n -= 1

                vn = v
                while n > 0:
                    vn = copy.deepcopy(vn)

                    name = vn['device_name']
                    vn['device_name'] = name[0:-1] + chr(ord(name[-1])+1)

                    if 'ephemeral' in vn:
                        ename = vn['ephemeral']
                        vn['ephemeral'] = ename[0:-1] + chr(ord(ename[-1])+1)

                    volumes.append(vn)
                    n -= 1

        j['volumes'] = volumes
        instances.append(j)

    return instances

# This filter sets the volume_id for any volumes that match existing attachable
# volumes as discovered by a tag search.

def match_existing_volumes(old_instances, cluster_name, ec2_volumes):
    instances = []

    for i in old_instances:
        for v in i.get('volumes', []):
            if not v.get('attach_existing', False):
                continue

            name = ':'.join([i['region'], cluster_name, str(i['node']), v['device_name']])
            if name in ec2_volumes:
                ev = ec2_volumes[name]

                if v['volume_size'] != ev['size'] or \
                    v.get('iops', ev['iops']) != ev['iops'] or \
                    v.get('volume_type', ev['type']) != ev['type']:
                    continue

                v['volume_id'] = ev['id']

        instances.append(i)

    return instances

# Takes a list of volumes and returns a new list where there is only one entry
# per device name (raid_device if defined, else device_name), consisting of the
# device name and any variables defined for it.
#
# The expanded list we start with looks like this:
#
# volumes:
#   - raid_device: /dev/md0
#     device_name: /dev/xvdb
#     vars:
#       mountpoint: /var/lib/postgresql
#     …
#   - raid_device: /dev/md0
#     device_name: /dev/xvdc
#     vars:
#       mountpoint: /var/lib/postgresql
#     …
#   - device_name: /dev/xvdd
#     vars:
#       mountpoint: /var/lib/barman
#     …
#
# And we end up with something like this:
#
# volumes:
#   - device: /dev/md0
#     mountpoint: /var/lib/postgresql
#   - device: /dev/xvdd
#     mountpoint: /var/lib/barman

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

# Given an instance definition, returns a dict of instance variables for the
# instance, comprising some instance settings (e.g., location, role, volumes),
# any settings mentioned in export_as_vars, and anything defined in vars (which
# takes precedence over everything else).
#
# For example, with the following instance definition:
#
# - node: 1
#   xyz: 123
#   pqr: 234
#   location: x
#   role: [a, b]
#   export_as_vars:
#     - xyz
#     - pqr
#   vars:
#     abc: 345
#
# it would return (a superset of):
#
# {abc: 345, xyz: 123, pqr: 234, location: x, role: [a, b], …}

def export_vars(instance):
    exports = {}

    always_export = ['location']
    for k in always_export + instance.get('export_as_vars', []):
        exports[k] = instance.get(k)

    export_if_set = ['backup', 'upstream']
    for k in export_if_set:
        v = instance.get(k)
        if v is not None:
            exports[k] = v

    exports['role'] = [x for x in instance.get('role', []) if x != 'postgres']

    exports['volumes'] = get_device_variables(instance.get('volumes', []))

    exports.update(instance.get('vars', {}))

    return exports

class FilterModule(object):
    def filters(self):
        return {
            'ip_addresses': ip_addresses,
            'set_instance_defaults': set_instance_defaults,
            'expand_instance_image': expand_instance_image,
            'expand_instance_volumes': expand_instance_volumes,
            'match_existing_volumes': match_existing_volumes,
            'export_vars': export_vars,
        }
