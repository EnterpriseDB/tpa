#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>
#
# The following two commands are roughly equivalent:
#
#   template.py template.j2 vars.yml \
#     $libdir/templates … > config.yml
#
#   ansible localhost -m template \
#     -a "src=template.j2 dest=config.yml" -e @vars.yml

import yaml
import os, io, sys
from ansible.template import Templar

class MinimalLoader(object):
    _basedir = []
    def __init__(self, basedir):
        self._basedir = basedir
    def get_basedir(self):
        return self._basedir

l = MinimalLoader([os.path.dirname(sys.argv[1])] + sys.argv[3:])
v = yaml.load(io.open(sys.argv[2], 'r'))
t = Templar(loader=l, variables=v)

sys.stdout.write(
    t.do_template(io.open(sys.argv[1], 'r').read())
)
