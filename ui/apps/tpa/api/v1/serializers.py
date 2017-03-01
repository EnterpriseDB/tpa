#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Serializers for TPA API Views.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from rest_framework import serializers

from tpa.config_yml import yml_to_cluster, DEFAULT_PROVIDER_NAME

logger = logging.getLogger(__name__)


class ConfigYmlSerializer(serializers.Serializer):
    '''Parse a config.yml and create a new cluster.
    '''
    tenant = serializers.CharField()
    config_yml = serializers.FileField()

    def create(self, validated_data):
        return yml_to_cluster(
            tenant_uuid=validated_data['tenant'],
            provider_name=DEFAULT_PROVIDER_NAME,
            yaml_text=validated_data['config_yml'])

    def update(self):
        raise NotImplementedError
