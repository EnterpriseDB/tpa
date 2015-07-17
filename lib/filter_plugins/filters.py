from jinja2.filters import contextfilter

def merge(a, b):
    return dict(a.items() + b.items());

# This is a poor substitute for map(attribute='x'), which Ansible does
# not currently support.

@contextfilter
def oneattr(context, seq, attr):
    func = lambda x: context.environment.getitem(x, attr)

    l = []
    if seq:
        for item in seq:
            l += func(item)

    return l

class FilterModule(object):
    def filters(self):
        return { 'merge' : merge, 'oneattr' : oneattr }
