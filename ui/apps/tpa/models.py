#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Cluster domain model.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.conf import settings
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
    class Meta(object):
        abstract = True

###


class Provider(BaseModel):
    name = CharField()


class Region(BaseModel):
    provider = ForeignKey('Provider')
    name = CharField()
    location = CharField()


class Zone(BaseModel):
    region = ForeignKey('Region')
    name = CharField()
    location = CharField()


class InstanceType(BaseModel):
    zone = ForeignKey('Zone')
    name = CharField()
    hardware_configuration = CharField()

##


class Tenant(BaseModel):
    name = CharField()


class TenantOwnedMixin(BaseModel):
    tentant = ForeignKey('Tenant')

    class Meta:
        abstract = True


class ProviderCredential(TenantOwnedMixin):
    provider = ForeignKey('Provider')
    name = CharField()
    shared_identity = CharField()
    shared_secret = CharField()


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
    name = CharField()
    cluster_type = CharField(choices=C_TYPES, max_length=1)


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
    name = CharField()


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
