#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

import copy
from jinja2 import Undefined
from jinja2.runtime import StrictUndefined
from ansible.errors import AnsibleFilterError

# This table is distilled from the content at
# https://aws.amazon.com/ec2/instance-types/

ephemeral_storage = {
    'm3.medium': 1, # 4GB
    'm3.large': 1, # 32GB
    'm3.xlarge': 2, # 40GB
    'm3.2xlarge': 2, # 80GB

    'c3.large': 2, # 16GB
    'c3.xlarge': 2, # 40GB
    'c3.2xlarge': 2, # 80GB
    'c3.4xlarge': 2, # 160GB
    'c3.8xlarge': 2, # 320GB

    'x1e.32xlarge': 2, # 1920GB
    'x1.32xlarge': 2, # 1920GB
    'x1.16xlarge': 1, # 1920GB

    'r3.large': 1, # 32GB
    'r3.xlarge': 1, # 80GB
    'r3.2xlarge': 1, # 160GB
    'r3.4xlarge': 1, # 320GB
    'r3.8xlarge': 2, # 320GB

    'f1.2xlarge': 1, # 470GB
    'f1.16xlarge': 4, # 940GB

    'i2.xlarge': 1, # 800GB
    'i2.2xlarge': 2, # 800GB
    'i2.4xlarge': 4, # 800GB
    'i2.8xlarge': 8, # 800GB

    'i3.large': 1, # 475GB
    'i3.xlarge': 1, # 950GB
    'i3.2xlarge': 1, # 1900GB
    'i3.4xlarge': 2, # 1900GB
    'i3.8xlarge': 4, # 1900GB
    'i3.16xlarge': 8, # 1900GB

    'd2.xlarge': 3, # 2000GB
    'd2.2xlarge': 6, # 2000GB
    'd2.4xlarge': 12, # 2000GB
    'd2.8xlarge': 24, # 2000GB
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

def set_instance_defaults(old_instances, cluster_name, instance_defaults):
    instances = []

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

        for kd in [k for k in instance_defaults if k != 'default_volumes']:
            j[kd] = j.get(kd, instance_defaults[kd])
            if isinstance(j[kd], dict) and isinstance(instance_defaults[kd], dict):
                b = copy.deepcopy(instance_defaults[kd])
                b.update(j[kd])
                j[kd] = b

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

# Given an instance definition, returns a dict mapping any keys mentioned in
# export_as_vars to the values set for the instance. For example, for an
# instance defined like this
#
# - node: 1
#   xyz: 123
#   pqr: 234
#   region: x
#   export_as_vars:
#     - xyz
#     - pqr
#   vars:
#     abc: 345
#
# it would return {xyz: 123, pqr: 234, region: x}, which could then be combined
# with vars. (Note that 'region' is always exported, regardless of whether it's
# mentioned in export_as_vars or not.)

def export_as_vars(instance):
    exports = {}

    always_export = ['region']
    for k in always_export + instance.get('export_as_vars', []):
        exports[k] = instance.get(k)

    return exports

class FilterModule(object):
    def filters(self):
        return {
            'ip_addresses': ip_addresses,
            'set_instance_defaults': set_instance_defaults,
            'expand_instance_image': expand_instance_image,
            'expand_instance_volumes': expand_instance_volumes,
            'match_existing_volumes': match_existing_volumes,
            'export_as_vars': export_as_vars,
        }
