#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

from __future__ import print_function

import copy
import boto3

from tpaexec.platform import Platform

class aws(Platform):
    def __init__(self, name, arch):
        super(aws, self).__init__(name, arch)
        self.ec2 = {}

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
        image = {}

        label = label.lower()

        if label in ['debian', 'debian-minimal']:
            image['name'] = 'debian-stretch-hvm-x86_64-gp2-2018-08-20-85640'
            image['owner'] = '379101102735'
            image['user'] = 'admin'
        elif label in ['redhat', 'redhat-minimal']:
            image['name'] = 'RHEL-7.5_HVM_GA-20180322-x86_64-1-Hourly2-GP2'
            image['owner'] = '309956199498'
            image['user'] = 'ec2-user'
        elif label in ['ubuntu', 'ubuntu-minimal']:
            image['name'] = 'ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20180814'
            image['owner'] = '099720109477'
            image['user'] = 'ubuntu'
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
            cluster_tags['Owner'] = args['owner']

    def update_locations(self, locations, args, **kwargs):
        region = args.get('region')
        subnets = args['subnets']
        for li, location in enumerate(locations):
            location['subnet'] = subnets[li]
            if region is not None:
                location['region'] = region
                location['az'] = region + ('a' if li%2 == 0 else 'b')

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
        s = args['platform_settings'] = {}

        s['ec2_vpc'] = {'Name': 'Test'}
        if args['image']:
            s['ec2_ami'] = {'Name': args['image']['name']}
            if 'owner' in args['image']:
                s['ec2_ami']['Owner'] = args['image']['owner']

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

        s['ec2_instance_reachability'] = 'public'
