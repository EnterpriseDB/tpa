#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © EnterpriseDB Corporation

import copy
import boto3
import sys

from tpaexec.platform import Platform

class aws(Platform):
    def __init__(self, name, arch):
        super().__init__(name, arch)
        self.ec2 = {}
        self.preferred_python_version = 'python3'

    def add_platform_options(self, p, g):
        if self.arch.name != 'Images':
            g.add_argument('--region', default='eu-west-1')
        g.add_argument('--instance-type', default='t3.micro', metavar='TYPE')

    def supported_distributions(self):
        return [
            'Debian', 'Debian-minimal',
            'RedHat', 'RedHat-minimal',
            'Ubuntu', 'Ubuntu-minimal',
        ]

    def default_distribution(self):
        return 'Debian'

    def image(self, label, **kwargs):
        images = {
            'debian': {
                'debian-jessie-amd64-hvm-2017-01-15-1221-ebs': {
                    'versions': ['8', 'jessie'],
                    'preferred_python_version': 'python2',
                    'owner': '379101102735',
                    'user': 'admin',
                },
                'debian-stretch-hvm-x86_64-gp2-2020-06-11-59901': {
                    'versions': ['9', 'stretch'],
                    'owner': '379101102735',
                    'user': 'admin',
                },
                'debian-10-amd64-20200610-293': {
                    'versions': ['10', 'buster', 'default'],
                    'owner': '136693071363',
                    'user': 'admin',
                },
            },
            'redhat': {
                'RHEL-7.8_HVM_GA-20200225-x86_64-1-Hourly2-GP2': {
                    'versions': ['7'],
                    'preferred_python_version': 'python2',
                    'owner': '309956199498',
                    'user': 'ec2-user',
                },
                'RHEL-8.2.0_HVM-20200423-x86_64-0-Hourly2-GP2': {
                    'versions': ['8', 'default'],
                    'owner': '309956199498',
                    'user': 'ec2-user',
                },
            },
            'ubuntu': {
                'ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20200610': {
                    'versions': ['16.04', 'xenial'],
                    'owner': '099720109477',
                    'user': 'ubuntu',
                },
                'ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-20200611': {
                    'versions': ['18.04', 'bionic', 'default'],
                    'owner': '099720109477',
                    'user': 'ubuntu',
                },
                'ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20200609': {
                    'versions': ['20.04', 'focal'],
                    'owner': '099720109477',
                    'user': 'ubuntu',
                },
            },
        }

        # Transform the table of known images into a form that allows for direct
        # lookup based on label and version.

        amis = {}
        for d in images:
            amis[d] = {}
            for n in images[d]:
                entry = images[d][n]
                for v in entry['versions']:
                    amis[d][v] = { 'name': n, **entry }

        image = {}

        if label in self.supported_distributions():
            label = label.replace('-minimal', '').lower()
            version = kwargs.get('version') or 'default'
            image = amis.get(label).get(version)
            if not image:
                print('ERROR: cannot determine AMI name for %s/%s' % (label, version), file=sys.stderr)
                sys.exit(-1)
            del image['versions']
            if 'preferred_python_version' in image:
                self.preferred_python_version = image['preferred_python_version']
                del image['preferred_python_version']
        else:
            image['name'] = label

        if kwargs.get('lookup', False):
            image.update(**self._lookup_ami(image, kwargs['region']))

        return image

    def _lookup_ami(self, image, region):
        if not region in self.ec2:
            self.ec2[region] = boto3.client('ec2', region_name=region)
        filters = [
            {'Name': 'name', 'Values': [image['name']]},
        ]
        if 'owner' in image:
            filters.append({
                'Name': 'owner-id', 'Values': [image['owner']],
            })
        v = self.arch.args['verbosity']
        if v > 0:
            print('aws: Looking up AMI "%s" in "%s"' % (image['name'], region))
        r = self.ec2[region].describe_images(Filters=filters)
        if v > 1:
            print('aws: Got lookup result: %s' % str(r))
        n = len(r['Images'])
        if n != 1:
            raise Exception('Expected 1 match for %s, found %d' % (image['name'], n))
        return {'image_id': r['Images'][0]['ImageId']}

    def update_cluster_tags(self, cluster_tags, args, **kwargs):
        if args['owner'] is not None:
            cluster_tags['Owner'] = \
                cluster_tags.get('Owner', args['owner'])

    def update_locations(self, locations, args, **kwargs):
        region = args.get('region')
        subnets = args['subnets']
        for li, location in enumerate(locations):
            location['subnet'] = \
                location.get('subnet', subnets[li])
            region = location.get('region', region)
            if region:
                location['region'] = region
                az = region + ('a' if li%2 == 0 else 'b')
                location['az'] = location.get('az', az)

    def update_cluster_vars(self, cluster_vars, args, **kwargs):
        cluster_vars['preferred_python_version'] = \
            cluster_vars.get('preferred_python_version', self.preferred_python_version)

    def update_instance_defaults(self, instance_defaults, args, **kwargs):
        y = self.arch.load_yaml('platforms/aws/instance_defaults.yml.j2', args)
        if y:
            instance_defaults.update(y)

    def update_instances(self, instances, args, **kwargs):
        for instance in instances:
            # For barman instances, convert the default postgres_data volume to
            # a correctly-sized barman_data one (if there isn't one already)
            role = instance.get('role') or []
            if 'barman' in role:
                instance_defaults = args.get('instance_defaults', {})
                default_volumes = instance_defaults.get('default_volumes', [])
                volumes = instance.get('volumes', [])

                barman_volume = {}
                for v in volumes:
                    volume_for = v.get('vars', {}).get('volume_for', '')
                    if volume_for == 'barman_data':
                        barman_volume = v

                default_barman_volume = {}
                default_postgres_volume = {}
                for v in default_volumes:
                    volume_for = v.get('vars', {}).get('volume_for', '')
                    if volume_for == 'postgres_data':
                        default_postgres_volume = v
                    elif volume_for == 'barman_data':
                        default_barman_volume = v

                if not (barman_volume or default_barman_volume) and default_postgres_volume:
                    v = copy.deepcopy(default_postgres_volume)
                    v['vars']['volume_for'] = 'barman_data'
                    size = self.arch.args.get('barman_volume_size')
                    if size is not None:
                        v['volume_size'] = size
                    instance['volumes'] = volumes + [v]

    def process_arguments(self, args):
        s = args.get('platform_settings') or {}

        ec2_vpc = {'Name': 'Test'}
        ec2_vpc.update(args.get('ec2_vpc', {}))
        s['ec2_vpc'] = ec2_vpc

        if args['image']:
            ec2_ami = {'Name': args['image']['name']}
            if 'owner' in args['image']:
                ec2_ami['Owner'] = args['image']['owner']
            ec2_ami.update(args.get('ec2_ami', {}))
            s['ec2_ami'] = ec2_ami

        cluster_rules = args.get('cluster_rules', [])
        if not cluster_rules and \
            'vpn_network' not in args['cluster_vars']:
            cluster_rules.append(
                dict(proto='tcp', from_port=22, to_port=22, cidr_ip='0.0.0.0/0')
            )
            for sn in args.get('subnets', []):
                cluster_rules.append(
                    dict(proto='tcp', from_port=0, to_port=65535, cidr_ip=sn)
                )
        if cluster_rules:
            s['cluster_rules'] = cluster_rules

        cluster_bucket = args.get('cluster_bucket')
        if cluster_bucket:
            s['cluster_bucket'] = cluster_bucket

        s['ec2_instance_reachability'] = 'public'

        args['platform_settings'] = s
