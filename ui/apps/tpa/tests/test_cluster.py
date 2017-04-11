#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Cluster model tests.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

import pytest

logger = logging.getLogger(__name__)


@pytest.mark.django_db()
def test_cluster_clone():
    from tpa.models import Cluster
    old_cluster = Cluster.objects.filter(provision_state='T').first()
    new_cluster = Cluster.clone(old_cluster,
                                name=old_cluster.name,
                                tenant=old_cluster.tenant)

    assert new_cluster


if __name__ == '__main__':
    import django
    django.setup()
    test_cluster_clone()
