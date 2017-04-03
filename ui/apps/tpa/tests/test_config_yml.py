#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Cluster model tests.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

import pytest

logger = logging.getLogger(__name__)


@pytest.mark.django_db(transaction=True)
def test_test_generate_yml():
    from tpa.models import Cluster
    from tpa.config_yml import generate_yml
    cluster = Cluster.objects.filter(provision_state='T').first()
    assert cluster is not None, "Couldn't get template cluster to test."
    generated_yaml = generate_yml(cluster)
    assert generated_yaml
    print(generated_yaml)


if __name__ == '__main__':
    import django
    django.setup()
    test_test_generate_yml()
