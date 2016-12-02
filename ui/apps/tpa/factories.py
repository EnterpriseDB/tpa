#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''
create
    cluster
        subnet
            instance
                role
                    link
'''

from __future__ import unicode_literals, absolute_import, print_function

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tpasite.conf.dev")

import logging
import factory
import tpa.models as m

logger = logging.getLogger(__name__)


class ClusterFactory(factory.DjangoModelFactory):
    class Meta:
        model = m.Cluster

if __name__ == '__main__':
    pass
