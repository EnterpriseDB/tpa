#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

import sys
import importlib

want = [
    'jinja2'
    , 'yaml'
    , 'cryptography'
    , 'dateutil'
    , 'setuptools'
    , 'netaddr'
    , 'six'
]
have = []

for m in want:
    try:
        importlib.import_module(m)
        have.append(m)
    except:
        pass

if len(have) < len(want):
    missing = [x for x in want if x not in have]
    print('ERROR: missing Python modules: ' + ', '.join(missing))
    if not hasattr(sys, 'real_prefix'):
        print('NOTE: %s is not running under a venv' % sys.executable)
    sys.exit(-1)

sys.exit(0)
