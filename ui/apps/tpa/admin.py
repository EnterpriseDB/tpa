#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''
'''

from __future__ import unicode_literals, absolute_import, print_function

from django.contrib import admin
from . import models

import logging

logger = logging.getLogger(__name__)

for class_name in models.__all__:
    admin.site.register(getattr(models, class_name))

if __name__ == '__main__':
    pass

