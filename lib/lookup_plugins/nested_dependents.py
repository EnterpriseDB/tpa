# This lookup plugin is similar to with_nested, but allows loop expressions to
# refer to earlier expressions as item.0, item.1, etc. Using it, you can write
# loops of this form:
#
#    for r in regions:
#        vpcs = get_vpcs_for_region(r)
#        for v in vpcs:
#            remove_vpc(r, v)
#
# This loop cannot be written using with_nested because vpcs cannot be evaluated
# without the value of the current region. Instead, it can be written as:
#
#    - ec2_vpc:
#        state: absent
#        region: "{{ item.0 }}"
#        vpc_id: "{{ item.1 }}"
#      with_nested_dependents:
#        - regions
#        - groups[cluster_tag]|intersect(groups[item.0])|map('lookup', hostvars, 'ec2_vpc_id')|unique|list
#
# Notice the reference to groups[item.0] in the second loop expression, where
# item.0 evaluates to the name of each region in turn, and therefore the task
# iterates over [r1, vpc-r1-1], [r1, vpc-r1-2], [r-2, vpc-r2-1], etc.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from jinja2.exceptions import UndefinedError

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        # We need to inject (and update) variables into the templar, but just
        # calling set_available_variables() won't work, because it copies the
        # supplied dict. We could just call it again after every update(), but
        # I can't bring myself to condone that much copying.

        self._templar.set_available_variables(variables)
        v = self._templar._available_variables

        # We start with an array of "terms", which are expressions that yield an
        # array or a single value when evaluated.

        if len(terms) == 0:
            raise AnsibleError("with_nested_dependents requires at least one element in the nested list")

        # We set the variable 'item' to an empty array and evaluate the first
        # term and recurse down the tree, re-evaluating sublists based on the
        # current value of 'item' (to which the current item from the current
        # term is appended each time we go deeper in the tree).

        return self.accumulate(v, [], terms[0], terms[1:])

    def accumulate(self, v, items, current_term, terms):

        v.update({'item': items})

        list = []
        results = []

        try:
            list = listify_lookup_plugin_terms(current_term,
                templar=self._templar, loader=self._loader,
                fail_on_undefined=True)
        except UndefinedError as e:
            raise AnsibleUndefinedVariable("Couldn't evaluate loop expression: %s" % e)

        if len(terms) == 0:
            results = [[i] for i in list]
        else:
            for item in list:
                sublist = self.accumulate(v, items + [item], terms[0], terms[1:])
                results += [[item]+t for t in sublist]

        return results
