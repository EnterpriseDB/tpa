#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Django config for test deployments.
'''

from __future__ import unicode_literals, absolute_import, print_function

from .local import *

DEBUG=True

DEPLOYMENT = 'test'

DATABASES['default']['NAME'] = "tpa-test"

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
    'rest_framework.renderers.BrowsableAPIRenderer'
)
