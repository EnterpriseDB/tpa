#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

from tpaexec.platform import Platform

class docker(Platform):
    def supported_distributions(self):
        return ['centos/systemd']

    def image(self, label, **kwargs):
        image = {}

        label = label.lower()

        if label in ['redhat', 'redhat-minimal']:
            image['name'] = 'centos/systemd'
        else:
            image['name'] = label

        return image

    def update_cluster_vars(self, cluster_vars, args, **kwargs):
        preferred_python_version = 'python3'
        if args['image']['name'] in ['centos/systemd']:
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
