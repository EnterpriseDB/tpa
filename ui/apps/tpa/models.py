#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Cluster domain model.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.conf import settings
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError
from django.db.models import (UUIDField, CharField, ForeignKey, BooleanField,
                              PositiveIntegerField)
from django.db import models


import uuid

logger = logging.getLogger(__name__)

# Mixins

class TextLineField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 255)
        super(TextLineField, TextLineField).__init__(self, *args, **kwargs)

LocationField = TextLineField


class UUIDMixin(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)

    class Meta(object):
        abstract = True


class TimestampMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        abstract = True


class BaseModel(UUIDMixin, TimestampMixin):
    name = TextLineField(db_index=True, blank=False)

    class Meta(object):
        abstract = True

###


class Provider(BaseModel):
    pass


class Region(BaseModel):
    provider = ForeignKey('Provider')
    location = LocationField(null=True)


class Zone(BaseModel):
    region = ForeignKey('Region')
    location = LocationField(null=True)


class InstanceType(BaseModel):
    zone = ForeignKey('Zone')
    hardware_configuration = TextLineField()


class VolumeType(BaseModel):
    provider = ForeignKey('Provider')

##


class Tenant(BaseModel):
    pass


class TenantOwnedMixin(BaseModel):
    tentant = ForeignKey('Tenant')
    user_tags = HStoreField()

    class Meta:
        abstract = True


class Cluster(TenantOwnedMixin):
    T_PG = 'P'
    T_BDR = 'B'
    T_XL = 'X'

    C_TYPES = (
        (T_PG, 'PostgreSQL'),
        (T_BDR, 'Bidirectional replication'),
        (T_XL, 'Postgres XL')
    )

    # Fields
    cluster_type = CharField(choices=C_TYPES, max_length=1)


class ProviderCredential(TenantOwnedMixin):
    provider = ForeignKey('Provider')
    shared_identity = TextLineField()
    shared_secret = TextLineField()


class Subnet(TenantOwnedMixin):
    cluster = ForeignKey('Cluster')
    zone = ForeignKey('Zone')
    credentials = ForeignKey('ProviderCredential')
    netmask = TextLineField()


class Instance(TenantOwnedMixin):
    subnet = ForeignKey('Subnet')
    instance_type = ForeignKey('InstanceType')

    hostname = TextLineField()
    domain = TextLineField()

    assign_eip = BooleanField(default=False)

    @property
    def fqdn(self):
        return self.hostname + '.' + self.domain


class Role(TenantOwnedMixin):
    instance = ForeignKey('Instance')


class RoleLink(TenantOwnedMixin):
    client_role = ForeignKey('Role', related_name='client_links')
    server_role = ForeignKey('Role', related_name='server_links')


class Volume(TenantOwnedMixin):
    instance = ForeignKey('Instance')
    volume_type = TextLineField()
    volume_size = PositiveIntegerField()
    delete_on_termination = BooleanField(default=False)

    class Meta:
        unique_together = (('instance', 'name'),)


class VolumeUse(TenantOwnedMixin):
    role = ForeignKey('Role')
    volume = ForeignKey('Volume')

    class Meta:
        unique_together = (('role', 'volume'),)
