#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''TPA config.yml command line loader.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from tpa.config_yml import yml_to_cluster

logger = logging.getLogger(__name__)

# Same as 500_example_cluster
TEST_TENANT = "d9073da2-138f-4342-8cb8-3462be0b325a"
TEST_PROVIDER = "EC2"


class Command(BaseCommand):
    help = 'Import config.yml files and generate clusters.'

    def add_arguments(self, parser):
        parser.add_argument('yaml', nargs='+', type=str)
        parser.add_argument('--tenant', '-t', nargs='?', type=str,
                            default=TEST_TENANT)
        parser.add_argument('--provider', '-p', nargs='?', type=str,
                            default=TEST_PROVIDER)

    def handle(self, *args, **options):
        with transaction.atomic():
            for yaml_file in options['yaml']:
                with open(yaml_file, 'r') as fd:
                    cluster = yml_to_cluster(
                        tenant_uuid=options['tenant'],
                        provider_name=options['provider'],
                        yaml_text=fd.read())

                print("New cluster ID:", cluster.uuid)
                print("Display URL: /cluster.html?cluster=%s"
                      % (cluster.uuid,))
