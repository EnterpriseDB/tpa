#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

from tpaexec.platform import Platform

class docker(Platform):
    def supported_distributions(self):
        return [
            'Debian', 'RedHat', 'Ubuntu',
        ]

    def default_distribution(self):
        return 'RedHat'

    def image(self, label, **kwargs):
        image = {}

        if label in self.supported_distributions():
            label = 'tpa/%s' % label.lower()
            version = kwargs.get('version')
            if version:
                label = label + ':' + version

        image['name'] = label

        return image

    def update_cluster_vars(self, cluster_vars, args, **kwargs):
        preferred_python_version = 'python3'
        if args['image']['name'] in ['centos/systemd', 'tpa/debian:8', 'tpa/redhat:7']:
            preferred_python_version = 'python2'
        cluster_vars['preferred_python_version'] = \
            cluster_vars.get('preferred_python_version', preferred_python_version)

    def update_instance_defaults(self, instance_defaults, args, **kwargs):
        y = self.arch.load_yaml('platforms/docker/instance_defaults.yml.j2', args)
        if y:
            instance_defaults.update(y)

    def update_instances(self, instances, args, **kwargs):
        for i in instances:
            newvolumes = []
            volumes = i.get('volumes', [])
            for v in volumes:
                if 'volume_type' in v and v['volume_type'] == 'none':
                    pass
                else:
                    newvolumes.append(v)
            if volumes:
                i['volumes'] = newvolumes

    def process_arguments(self, args):
        s = args.get('platform_settings') or {}

        docker_images = args.get('docker_images')
        if docker_images:
            s['docker_images'] = docker_images

        args['platform_settings'] = s
