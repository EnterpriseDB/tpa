import copy
from jinja2 import Undefined
from jinja2.runtime import StrictUndefined

# This filter takes an array of hashes and returns a new array in which every
# entry in the original array is represented by item[instance_count] entries.
# Furthermore, each entry has item[node] set to an increasing counter.

def expand_instances(a):
    c = []
    idx = 1
    for x in a:
        inst_count = 0
        # check if instance_count has been specified, default to 1 if not
        try:
            x['instance_count']
        except KeyError:
            x['instance_count'] = 1

        exact_count = x['instance_count']
        while (inst_count < exact_count):
            y = copy.deepcopy(x)
            y['node'] = idx
            y['role'] = y['role'] or []
            c.append(y)
            inst_count = inst_count + 1
            idx = idx + 1
    return c

# Given an array of volumes (as defined in instances[]), this filters sets
# delete_on_termination to true unless it's been explicitly set to false.
# Also translates a device name of "root" to the given root device name.

def define_volumes(v, root_device_name):
    if isinstance(v, list):
        for i in v:
            if not 'delete_on_termination' in i:
                i['delete_on_termination'] = True
            if i['device_name'] == 'root':
                i['device_name'] = root_device_name
    return v

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

class FilterModule(object):
    def filters(self):
        return {
            'expand_instances': expand_instances,
            'try_subkey': try_subkey,
            'define_volumes': define_volumes,
        }
