#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Django config for dev.
'''

from __future__ import unicode_literals, absolute_import, print_function

from .test import *

DEPLOYMENT = 'test'

DATABASES['default']['name'] = "tpa-test"
