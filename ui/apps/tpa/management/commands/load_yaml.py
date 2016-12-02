#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging


from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from yaml import Loader, load as yaml_load

import tpa.models as m

logger = logging.getLogger(__name__)

TEST_TENANT = "d9073da2-138f-4342-8cb8-3462be0b325a"
TEST_PROVIDER = "EC2"


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('yaml', nargs='+', type=str)

    def handle(self, *args, **options):
        tenant = m.Tenant.objects.get(uuid=TEST_TENANT)
        provider = m.Provider.objects.get(name='EC2')

        creds = m.ProviderCredential.objects.get(provider=provider,
                                                   tenant=tenant)

        if creds:
            creds = creds
        else:
            creds = m.ProviderCredential.objects.create(
                provider=provider,
                tenant=tenant,
                name='Dummy EC2 Creds',
                shared_identitity='AK',
                shared_secret='SAK')

        for yaml_file in options['yaml']:
            with open(yaml_file, 'r') as fd:
                root = yaml_load(fd.read(), Loader)
            with transaction.atomic():
                cluster = self.generate_cluster(root, tenant, provider, creds)
                assert "Skipping Create"


    def generate_cluster(self, root, tenant, provider, creds):
        upstreams = {}
        subnets = {}
        instance_by_name = {}
        backups = {}

        cluster = m.Cluster.objects.create(
            tenant=tenant,
            name=root["cluster_name"],
            user_tags = root['cluster_tags'])

        vpc = m.VPC.objects.create(
            name=root["ec2_vpc"]["Name"],
            provider=provider,
            cluster=cluster,
            tenant=tenant,
        )

        for (region_name, region_subnets) in root['ec2_vpc_subnets'].iteritems():
            region = m.Region.objects.get(provider=provider,
                                          name=region_name)
            for netmask, subnet in region_subnets.iteritems():
                subnets[netmask] = m.Subnet.objects.create(
                    name=netmask,
                    netmask=netmask,
                    zone=m.Zone.objects.get(region=region,
                                            name=subnet["az"]),
                    cluster=cluster,
                    tenant=tenant,
                    vpc=vpc,
                    credentials=creds
                )

        print("Subnets:", subnets)

        for ins_def in root["instances"]:
            subnet = subnets[ins_def['subnet']]
            instance = m.Instance.objects.create(
                tenant=tenant,
                subnet=subnet,
                name=ins_def['tags']['Name'],
                instance_type=m.InstanceType.objects.get(
                    zone=subnet.zone,
                    name=ins_def['type']),
                hostname="",
                domain="",
                assign_eip=ins_def.get('assign_eip', False))

            instance_by_name[instance.name] = instance

            if ins_def.get('upstream'):
                upstreams.append((ins_def['upstream'], instance))

            if ins_def.get('backup'):
                backups.append((ins_def['backup'], instance))

        # TODO Roles, Links - Upstream, Backups


