#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Serializers for TPA API Views.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.db import transaction
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.serializers import UUIDField, CharField, ModelSerializer

from tpa import models
from tpa.config_yml import yml_to_cluster, DEFAULT_PROVIDER_NAME

logger = logging.getLogger(__name__)


def validate_tenant_for_cluster_create(view, value):
    request = view.context['request']
    user = request.user
    default_tenant = models.Tenant.for_request(request)

    if not value:
        return default_tenant

    tenant = models.Tenant.objects.get(uuid=value)

    if tenant.uuid != default_tenant.uuid:
        if tenant.owner == user or user.is_staff or user.is_admin:
            return tenant

    raise serializers.ValidationError("Not allowed to change ownership")


class ConfigYmlSerializer(ModelSerializer):
    '''Parse a config.yml and create a new cluster.
    '''
    uuid = UUIDField(read_only=True)
    name = CharField(required=False)
    tenant = UUIDField(required=False, write_only=True)
    config_yml = serializers.FileField(required=True, write_only=True)

    class Meta:
        model = models.Cluster
        fields = ('uuid', 'name', 'tenant', 'config_yml')

    validate_tenant = validate_tenant_for_cluster_create

    def create(self, validated_data):
        tenant = (validated_data.get('tenant') or self.validate_tenant(None))

        cluster = yml_to_cluster(
            tenant_uuid=tenant.uuid,
            provider_name=DEFAULT_PROVIDER_NAME,
            yaml_text=validated_data['config_yml'])

        if 'name' in validated_data:
            cluster.name = validated_data['name']
            cluster.save()

        return cluster

    def update(self, *args, **kwargs):
        raise NotImplementedError


class ClusterFromTemplateSerializer(ModelSerializer):
    uuid = UUIDField(read_only=True)
    name = CharField(required=False)
    tenant = UUIDField(required=False, write_only=True)
    template = UUIDField(required=True, write_only=True)

    class Meta:
        model = models.Cluster
        fields = ('uuid', 'name', 'tenant', 'template')

    validate_tenant = validate_tenant_for_cluster_create

    def validate_template(self, value):
        return models.Cluster.objects.get(
            uuid=value,
            provision_state=models.Cluster.P_TEMPLATE)

    def create(self, validated_data):
        return models.Cluster.clone(
            validated_data['template'],
            name=validated_data.get('name') or validated_data['template'].name,
            tenant=validated_data.get('tenant') or self.validate_tenant(None))

    def update(self, *args, **kwargs):
        raise NotImplementedError


class UserInvitationSerializer(ModelSerializer):
    email = serializers.EmailField(required=True)
    new_tenant_name = CharField(required=False)

    class Meta:
        model = models.UserInvitation
        fields = ('email', 'new_tenant_name')

    def create(self, data):
        return models.UserInvitation.objects.create(
            email=data['email'],
            new_tenant_name=data.get("new_tenant_name") or data['email'],
        )


class UserInvitedRegistrationSerializer(ModelSerializer):
    invite = UUIDField()
    ssh_public_keys = serializers.ListField(child=CharField(allow_blank=True))

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'first_name', 'last_name',
                  'password', 'ssh_public_keys', 'invite')
        write_only_fields = ('password', 'invite')
        read_only_fields = ('is_staff', 'is_superuser',
                            'is_active', 'date_joined', 'id')

    def update(self, instance, data):
        with transaction.atomic():
            instance.set_password(data['password'])
            instance.username = data['username']
            instance.first_name = data.get('first_name', '')
            instance.last_name = data.get('last_name', '')
            instance.is_active = True
            instance.save()

            tenant = models.Tenant.objects.get(owner=instance)
            tenant.ssh_public_keys = data['ssh_public_keys']
            tenant.save()

            self._invite.delete()

        return instance

    def delete(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def get(self, *args, **kwargs):
        raise NotImplementedError
