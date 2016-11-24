#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Add support for PostgreSQL HSTORE fields.
'''

from __future__ import unicode_literals, absolute_import, print_function

from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations


class Migration(migrations.Migration):
    operations = [
        HStoreExtension(),
    ]
