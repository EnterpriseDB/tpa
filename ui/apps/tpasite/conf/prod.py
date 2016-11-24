#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Configuration for production.
'''

from __future__ import unicode_literals, absolute_import, print_function

from .local import *

DEPLOYMENT = 'prod'

DATABASES['default']['NAME'] = 'tpa-prod'
