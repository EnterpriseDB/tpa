def merge(a, b):
    return dict(a.items() + b.items());

class FilterModule(object):
    def filters(self):
        return { 'merge' : merge }
