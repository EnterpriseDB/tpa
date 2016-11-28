import copy
from jinja2 import Undefined
from jinja2.runtime import StrictUndefined

# This filter takes an array of instance definitions and returns a new
# array with each instance adjusted to have the expected tags.

def expand_instance_tags(a):
    c = []
    for x in a:
        y = copy.deepcopy(x)
        y['tags'] = y.get('tags', {})

        # The 'Name' tag specifies the hostname of the instance, so it
        # should not contain underscores. Also translate name to Name
        # for convenience.

        if 'name' in y['tags'] and not 'Name' in y['tags']:
            y['tags']['Name'] = y['tags']['name']
            del y['tags']['name']
        if 'Name' in y['tags']:
            y['tags']['Name'] = y['tags']['Name'].replace('_','-').lower()

        # The role tag should be a list, so we convert comma-separated
        # strings if that's what we're given.

        y['tags']['role'] = y['tags'].get('role', [])
        if not isinstance(y['tags']['role'], list):
            y['tags']['role'] = map(lambda x: x.strip(), y['tags']['role'].split(","))

        # primary/replica instances must also be tagged 'postgres'.

        if ('primary' in y['tags']['role'] or 'replica' in y['tags']['role']) and \
            not 'postgres' in y['tags']['role']:
            y['tags']['role'] = y['tags']['role'] + ['postgres']

        c.append(y)
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

# Given 'foo', returns '"foo"'. Blindly converts each embedded double quote in
# the string to '\"'. Caveat emptor.

def doublequote(str):
    return '"%s"' % str.replace('"', '\"')

# Given a hostname and hostvars, returns the name of the earliest ancestor that
# doesn't have an upstream defined.

def upstream_root(root, hostvars):
    while root in hostvars and hostvars[root].get('upstream', '') != '':
        root = hostvars[root].get('upstream')
    return root

class FilterModule(object):
    def filters(self):
        return {
            'expand_instance_tags': expand_instance_tags,
            'try_subkey': try_subkey,
            'define_volumes': define_volumes,
            'doublequote': doublequote,
            'upstream_root': upstream_root,
        }
