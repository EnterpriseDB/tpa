#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Cluster domain model.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.conf import settings
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError
from django.db.models import (UUIDField, CharField, ForeignKey)
from django.db import models


import uuid

logger = logging.getLogger(__name__)

# Mixins


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
    name = CharField()

    class Meta(object):
        abstract = True

###


class Provider(BaseModel):
    pass


class Region(BaseModel):
    provider = ForeignKey('Provider')
    location = CharField()


class Zone(BaseModel):
    region = ForeignKey('Region')
    location = CharField()


class InstanceType(BaseModel):
    zone = ForeignKey('Zone')
    hardware_configuration = CharField()

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
    shared_identity = CharField()
    shared_secret = CharField()


class Subnet(TenantOwnedMixin):
    cluster = ForeignKey('Cluster')
    zone = ForeignKey('Zone')
    credentials = ForeignKey('ProviderCredential')
    netmask = CharField()


class Instance(TenantOwnedMixin):
    subnet = ForeignKey('Subnet')
    instance_type = ForeignKey('InstanceType')

    hostname = CharField()
    domain = CharField()


class Role(TenantOwnedMixin):
    instance = ForeignKey('Instance')


class RoleLink(TenantOwnedMixin):
    client_role = ForeignKey('Role')
    server_role = ForeignKey('Role')


class Volume(TenantOwnedMixin):
    instance = ForeignKey('Instance')
    mount_point = CharField()
    size = CharField()

    class Meta:
        unique_together = (('instance', 'mount_point'),)


class VolumeUse(TenantOwnedMixin):
    role = ForeignKey('Role')
    volume = ForeignKey('Volume')

    class Meta:
        unique_together = (('role', 'volume'),)
