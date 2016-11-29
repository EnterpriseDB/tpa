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

def upstream_root(root, hostvars):
    while root in hostvars and hostvars[root].get('upstream', '') != '':
        root = hostvars[root].get('upstream')
    return root

class FilterModule(object):
    def filters(self):
        return {
            'try_subkey': try_subkey,
            'doublequote': doublequote,
            'upstream_root': upstream_root,
        }
