#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''TPA config.yml loader.
'''

from __future__ import unicode_literals, absolute_import, print_function

import types
import logging


from django.core.management.base import BaseCommand
from django.db import transaction
from yaml import Loader, load as yaml_load

import tpa.models as m

logger = logging.getLogger(__name__)

# Same as 500_example_cluster
TEST_TENANT = "d9073da2-138f-4342-8cb8-3462be0b325a"
TEST_PROVIDER = "EC2"

FWD, REV = True, False

# Link direction, type, client role, server role
ROLE_LINKS = [
    # TPA cluster
    (FWD, 'upstream', 'replica', 'primary'),
    (FWD, 'upstream', 'replica', 'replica'),
    (REV, 'backup', 'replica', 'barman'),
    (REV, 'backup', 'primary', 'barman'),
    # TODO BDR Cluster
    (REV, 'backup', 'bdr', 'barman'),
    (REV, 'log', 'bdr', 'log-server'),
    (REV, 'control', 'bdr', 'control'),
]

IMPLICIT_ROLE_LINKS = [
    (FWD, 'gtm', 'coordinator', 'gtm'),
    (FWD, 'coordinator', 'datanode', 'coordinator'),
    (FWD, 'coordinator', 'datanode-replica', 'coordinator'),
]


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('yaml', nargs='+', type=str)
        parser.add_argument('--tenant', '-t', nargs='?', type=str,
                            default=TEST_TENANT)
        parser.add_argument('--provider', '-p', nargs='?', type=str,
                            default=TEST_PROVIDER)

    def handle(self, *args, **options):
        tenant = m.Tenant.objects.get(uuid=options['tenant'])
        provider = m.Provider.objects.get(name=options['provider'])
        creds = m.ProviderCredential.objects.filter(provider=provider,
                                                  tenant=tenant)

        if not creds:
            creds = m.ProviderCredential.objects.create(
                provider=provider,
                tenant=tenant,
                name='Dummy EC2 Creds',
                shared_identity='AK',
                shared_secret='SAK')
        else:
            creds = creds[0]

        for yaml_file in options['yaml']:
            cluster = None
            with open(yaml_file, 'r') as fd:
                root = yaml_load(fd.read(), Loader)
            with transaction.atomic():
                cluster = self.generate_cluster(root, tenant, provider, creds)
            print("New cluster ID:", cluster.uuid)
            print("Display URL: /cluster.html?cluster=%s" % (cluster.uuid,));

    def generate_cluster(self, root, tenant, provider, creds):
        subnets = {}
        roles = {}
        links = []  # client instance, role_name, server instance, role_name

        # XL
        dn_roles = {}   # id -> dn_role
        dnr_roles = {}  # id -> dnr_role
        gtm_roles = []
        coord_roles = []

        cluster = m.Cluster.objects.create(
            tenant=tenant,
            name=root["cluster_name"],
            user_tags=root['cluster_tags'])

        vpc = m.VPC.objects.create(
            name=root["ec2_vpc"]["Name"],
            provider=provider,
            cluster=cluster,
            tenant=tenant,
        )

        for (region_name, region_subnets) \
                in root['ec2_vpc_subnets'].iteritems():
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

        for ins_def in root["instances"]:
            ins_tags = ins_def['tags']
            subnet_cidr = ins_def['subnet']
            if subnet_cidr in subnets:
                subnet = subnets[subnet_cidr]
            else:
                # Create implicit subnet
                subnet = subnets[subnet_cidr] = m.Subnet.objects.create(
                    name=subnet_cidr,
                    netmask=subnet_cidr,
                    zone=subnets.values()[0].zone,
                    cluster=cluster,
                    tenant=tenant,
                    vpc=subnets.values()[0].vpc,
                    credentials=creds)

            instance = m.Instance.objects.create(
                tenant=tenant,
                subnet=subnet,
                name=ins_tags.get('Name', ("node-%s" % ins_def['node'])),
                instance_type=m.InstanceType.objects.get(
                    zone=subnet.zone,
                    name=ins_def['type']),
                hostname="",
                domain="",
                assign_eip=ins_def.get('assign_eip', False))

            # Roles: names can be in CSV or expanded list.
            role_names = ins_tags.get('role', [])
            if type(role_names) in types.StringTypes:
                role_names = role_names.split(',')

            for role_name in role_names:
                role_name = role_name.strip()

                if not role_name:
                    continue

                if role_name == 'datanode':
                    # generate one role per dn index
                    for dn_id in ins_tags.get('dn_list', "").split(','):
                        dn_name = ('%s-%s' % (role_name, dn_id,))
                        role = m.Role.objects.create(
                            instance=instance,
                            tenant=tenant,
                            name=dn_name,
                            role_type=role_name)
                        roles[(instance.name, dn_name)] = role
                        dn_roles[dn_id] = role
                elif role_name == 'datanode-replica':
                    for dn_id in ins_tags.get('dn_replica_list', "").split(','):
                        dnr_name = ('%s-%s' % (role_name, dn_id,))
                        role = m.Role.objects.create(
                                instance=instance,
                                tenant=tenant,
                                name=dnr_name,
                                role_type=role_name)
                        roles[(instance.name, dnr_name)] = role
                        dnr_roles[dn_id] = role
                else:
                    role = m.Role.objects.create(
                        instance=instance,
                        tenant=tenant,
                        name=role_name,
                        role_type=role_name)

                    roles[(instance.name, role_name)] = role

                    if role_name == 'gtm':
                        gtm_roles.append(role)
                    elif role_name == 'coordinator':
                        coord_roles.append(role)

            # Role links (deferred)
            for (dirn, rel_name, client_role, server_role) in ROLE_LINKS:
                if rel_name in ins_tags and client_role in role_names:
                    links.append((dirn, rel_name,
                                  instance.name, client_role,
                                  ins_tags[rel_name], server_role),)

            # Volumes
            for vol_def in ins_def.get('volumes', []):
                if 'ephemeral' in vol_def:
                    vol_type = 'ephemeral'
                else:
                    vol_type = vol_def['volume_type']

                volume = m.Volume.objects.create(
                    tenant=tenant,
                    instance=instance,
                    name=vol_def['device_name'],
                    volume_type=m.VolumeType.objects.get(
                        provider=provider,
                        name=vol_type
                    ).name,
                    volume_size=vol_def.get('volume_size', "0"),
                    delete_on_termination=vol_def.get('delete_on_termination',
                                                      True)
                )

                # EC2 ephemeral volume
                if 'ephemeral' in vol_def:
                    volume.user_tags = {
                        'ephemeral': vol_def['ephemeral']
                    }
                    volume.save()

        # Links
        for (dirn, rel_name,
             client_name, client_role,
             server_name, server_role) in links:

            if (server_name, server_role) not in roles:
                print("skipping",
                      rel_name, client_name, client_role,
                      server_name, server_role)
                continue

            server_role = roles[(server_name, server_role)]
            client_role = roles[(client_name, client_role)]

            if dirn == REV:
                (server_role, client_role) = (client_role, server_role)

            m.RoleLink.objects.create(
                tenant=tenant,
                name=rel_name,
                server_role=server_role,
                client_role=client_role)

        # XL links
        for (dn_idx, dnr_role) in dnr_roles.iteritems():
            m.RoleLink.objects.create(
                tenant=tenant,
                name='datanode-replica',
                server_role=dn_roles[dn_idx],
                client_role=dnr_role)

            for coord_role in coord_roles:
                m.RoleLink.objects.create(
                    tenant=tenant,
                    name='coordinator',
                    server_role=coord_role,
                    client_role=dnr_role)

        for (dn_idx, dn_role) in dn_roles.iteritems():
            for coord_role in coord_roles:
                m.RoleLink.objects.create(
                    tenant=tenant,
                    name='coordinator',
                    server_role=coord_role,
                    client_role=dn_role)

        for coord_role in coord_roles:
            for gtm_role in gtm_roles:
                m.RoleLink.objects.create(
                    tenant=tenant,
                    name='gtm',
                    server_role=gtm_role,
                    client_role=coord_role)

        return cluster
