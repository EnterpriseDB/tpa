#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.
#
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
#        - groups[cluster_tag]|intersect(groups[item.0])|map('extract', hostvars, 'ec2_vpc_id')|unique|list
#
# Notice the reference to groups[item.0] in the second loop expression, where
# item.0 evaluates to the name of each region in turn, and therefore the task
# iterates over [r1, vpc-r1-1], [r1, vpc-r1-2], [r-2, vpc-r2-1], etc.

from jinja2.exceptions import UndefinedError

from collections import Iterable
from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        v = variables.copy()
        self._templar.set_available_variables(v)

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
            expr = current_term
            convert_bare = False

            if isinstance(current_term, str):
                expr = expr.strip()
                convert_bare = True

            list = self._templar.template(expr, cache=False,
                fail_on_undefined=False, convert_bare=convert_bare)

            if isinstance(list, str) or not isinstance(list, Iterable):
                list = [list]
        except UndefinedError as e:
            raise AnsibleUndefinedVariable("Couldn't evaluate loop expression: %s" % e)

        if len(terms) == 0:
            results = [[i] for i in list]
        else:
            for item in list:
                sublist = self.accumulate(v, items + [item], terms[0], terms[1:])
                results += [[item]+t for t in sublist]

        return results
