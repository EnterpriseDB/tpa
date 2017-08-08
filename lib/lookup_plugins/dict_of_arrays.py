from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import collections

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        # Expect any type of Mapping, notably hostvars
        if not isinstance(terms, collections.Mapping):
            raise AnsibleError("with_dict_of_arrays expects a dict")

        ret = []
        for key in terms:
            values = terms[key]

            if not isinstance(values, list):
                values = [values]

            for v in values:
                ret.append({'key': key, 'value': v})

        return ret
