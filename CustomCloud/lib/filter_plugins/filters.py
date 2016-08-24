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
            c.append(y)
            inst_count = inst_count + 1
            idx = idx + 1
    return c

# This filter takes an item and a container, and returns the value of the item
# in the container (i.e. a key in a dict or an index in a list). It optionally
# takes an array of keys to look up recursively in the first result:
#
# ['a', 'b']|map('extract', {'a': 21, 'b': 42})|list
# groups['x']|map('extract', hostvars, 'ec2_id')|list

def extract(item, container, morekeys=None):
    value = container[item]

    if value is not Undefined and morekeys is not None:
        if not isinstance(morekeys, list):
            morekeys = [morekeys]

        value = reduce(lambda d, k: d[k], morekeys, value)

    return value

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
            'extract': extract,
            'expand_instances': expand_instances,
            'try_subkey': try_subkey,
        }
