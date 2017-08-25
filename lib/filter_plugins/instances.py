import copy
from jinja2 import Undefined
from jinja2.runtime import StrictUndefined

## Instance filters
#
# The filters defined here take the array of instances (from config.yml)
# and other inputs and return a new array of instances with parameters
# suitably adjusted.

# Every instance must have tags; some tags must be in a specific format.

def expand_instance_tags(old_instances, cluster_name):
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

            if v['device_name'] == 'root':
                v['device_name'] = ec2_ami_properties[j['image']]['root_device_name']
            if not 'delete_on_termination' in v:
                v['delete_on_termination'] = not v.get('attach_existing',False)

            volumes.append(v)

            # If the entry specifies raid_device, then we repeat this volume
            # raid_units-1 times.

            if 'raid_device' in v:
                n = v['raid_units'] - 1

                vn = v
                while n > 0:
                    vn = copy.deepcopy(vn)

                    name = vn['device_name']
                    vn['device_name'] = name[0:-1] + chr(ord(name[-1])+1)

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

class FilterModule(object):
    def filters(self):
        return {
            'expand_instance_tags': expand_instance_tags,
            'expand_instance_image': expand_instance_image,
            'expand_instance_volumes': expand_instance_volumes,
            'match_existing_volumes': match_existing_volumes,
        }
