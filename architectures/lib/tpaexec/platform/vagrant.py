#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

from __future__ import print_function

# Required for backwards compatibility with Python2
from six import u as unicode

import ipaddress

from tpaexec.platform import Platform

class vagrant(Platform):
    def add_platform_options(self, p, g):
        g.add_argument(
            '--provider', default='virtualbox', choices=['virtualbox'],
            help='virtualbox is currently the only supported provider',
        )
        g.add_argument('--memory', type=int, metavar='MB')
        g.add_argument(
            '--proxyconf', metavar='PROXY',
            help='[vagrant-proxyconf] proxy URL to configure on VMs',
        )
        g.add_argument(
            '--inject-ca-certificates', metavar='DIR', dest='capath',
            help='[vagrant-ca-certificates] CA certificates to configure on VMs',
        )

    def supported_distributions(self):
        return [
            'Debian', 'RedHat', 'Ubuntu',
        ]

    def default_distribution(self):
        return 'Debian'

    def image(self, label, **kwargs):
        image = {}
        images = {
            'debian': 'debian/stretch64',
            'redhat': 'centos/7',
            'ubuntu': 'ubuntu/bionic64',
        }

        label = label.lower()
        image['name'] = images.get(label, label)
        image['user'] = 'admin'
        return image

    def update_instance_defaults(self, instance_defaults, args, **kwargs):
        if args['memory']:
            instance_defaults.update({
                'memory': args['memory']
            })
        instance_defaults.update({
            'image': args['image']['name']
        })

    def update_instances(self, instances, args, **kwargs):
        addresses = list(ipaddress.ip_network(unicode(args['subnets'][0])).hosts())

        for i,instance in enumerate(instances):
            instance['ip_address'] = str(addresses[i+1])

    def process_arguments(self, args):
        s = {}

        if args['proxyconf']:
            s['vagrant_proxyconf'] = args['proxyconf']
        if args['capath']:
            s['vagrant_ca_certificates'] = args['capath']

        if s:
            args['platform_settings'] = s
