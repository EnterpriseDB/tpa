#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from tpaexec.platform import Platform

class docker(Platform):
    def supported_distributions(self):
        return ['centos/systemd']

    def image(self, label, **kwargs):
        return {'name': label}

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
