#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Cluster domain model.
'''

from __future__ import absolute_import, print_function, unicode_literals

import logging
from uuid import uuid4

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import (BooleanField, CharField, DateTimeField,
                              ForeignKey, PositiveIntegerField, UUIDField)

logger = logging.getLogger(__name__)

__all__ = '''
Provider Region Zone InstanceType VolumeType
Tenant Cluster ProviderCredential Subnet
Instance Role RoleLink Volume VolumeUse VPC
'''.split()


# Mixins


class TextLineField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 255)
        super(TextLineField, TextLineField).__init__(self, *args, **kwargs)


LocationField = TextLineField


class OwnerKey(ForeignKey):
    pass


class UUIDMixin(models.Model):
    uuid = UUIDField(primary_key=True, default=uuid4, editable=False)

    class Meta(object):
        abstract = True


class TimestampMixin(models.Model):
    created = DateTimeField(auto_now_add=True, editable=False)
    updated = DateTimeField(auto_now=True, editable=False)

    class Meta(object):
        abstract = True


class BaseModel(UUIDMixin, TimestampMixin):
    name = TextLineField(db_index=True, blank=True)
    description = TextLineField(blank=True)

    class Meta(object):
        abstract = True

###


class Provider(BaseModel):
    owned_fields = ('regions',)


class Region(BaseModel):
    provider = OwnerKey('Provider', related_name='regions')
    location = LocationField(null=True)


class Zone(BaseModel):
    region = OwnerKey('Region', related_name='zones')
    location = LocationField(null=True)


class InstanceType(BaseModel):
    zone = OwnerKey('Zone', related_name="instance_types")
    hardware_configuration = TextLineField()


class VolumeType(BaseModel):
    provider = OwnerKey('Provider', related_name="volume_types")


##


class Tenant(BaseModel):
    pass


class TenantOwnedMixin(BaseModel):
    tenant = ForeignKey('Tenant', editable=False)
    user_tags = JSONField(default={})

    class Meta:
        abstract = True


class Cluster(TenantOwnedMixin):
    #tenant = OwnerKey('Tenant', editable=False)
    pass


class ProviderCredential(TenantOwnedMixin):
    provider = ForeignKey('Provider', related_name='credentials')
    shared_identity = TextLineField()
    shared_secret = TextLineField()


class VPC(TenantOwnedMixin):
    cluster = OwnerKey('Cluster')
    provider = ForeignKey('Provider', related_name='vpcs')


class Subnet(TenantOwnedMixin):
    cluster = OwnerKey('Cluster', related_name='subnets')
    zone = ForeignKey('Zone', related_name='subnets')
    vpc = ForeignKey('VPC', related_name='subnets')
    credentials = ForeignKey('ProviderCredential', related_name='subnets')
    netmask = TextLineField()


class Instance(TenantOwnedMixin):
    subnet = OwnerKey('Subnet', related_name='instances')
    instance_type = ForeignKey('InstanceType', related_name='instances')

    hostname = TextLineField()
    domain = TextLineField()

    assign_eip = BooleanField(default=False)

    @property
    def fqdn(self):
        return self.hostname + '.' + self.domain


class Role(TenantOwnedMixin):
    instance = OwnerKey('Instance', related_name='roles')


class RoleLink(TenantOwnedMixin):
    client_role = OwnerKey('Role', related_name='client_links')
    server_role = ForeignKey('Role', related_name='server_links')

    class Meta:
        unique_together = (('client_role', 'server_role'),)


class Volume(TenantOwnedMixin):
    instance = ForeignKey('Instance', related_name='volumes')
    volume_type = TextLineField()
    volume_size = PositiveIntegerField()
    delete_on_termination = BooleanField(default=True)

    class Meta:
        unique_together = (('instance', 'name'),)


class VolumeUse(TenantOwnedMixin):
    role = ForeignKey('Role', related_name='used_volumes')
    volume = ForeignKey('Volume', related_name='used_by_roles')

    class Meta:
        unique_together = (('role', 'volume'),)
