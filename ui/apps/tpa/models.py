#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Cluster domain model.
'''

from __future__ import absolute_import, print_function, unicode_literals

import logging
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
#from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import (BooleanField, CharField, DateTimeField,
                              ForeignKey, PositiveIntegerField, TextField,
                              UUIDField)
from django.utils.translation import gettext_lazy as _

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

    def __unicode__(self):
        return unicode(self.name or self.uuid)

    @classmethod
    def clone(cls, __source, link_map=None, role_map=None, **kwargs):
        new_obj = __source.__class__.objects.get(uuid=__source.uuid)
        new_obj.uuid = None
        new_obj.created = None
        new_obj.updated = None

        for (field, value) in kwargs.iteritems():
            setattr(new_obj, field, value)

        new_obj.save()

        return new_obj

# Provider


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
    hardware = JSONField(default="")
    vcpus = PositiveIntegerField(null=True)
    memory = PositiveIntegerField(null=True)


class VolumeType(BaseModel):
    provider = OwnerKey('Provider', related_name="volume_types")


# User

class UserInvitation(UUIDMixin, TimestampMixin):
    '''An invitation to an unregistered user
    '''
    email = models.EmailField(unique=True)
    user_id = TextField(unique=True)
    new_tenant_name = TextField(null=True)


# Tenant

class Tenant(BaseModel):
    owner = ForeignKey(settings.AUTH_USER_MODEL, editable=True,
                       on_delete=models.CASCADE,
                       null=True)
    ssh_public_keys = ArrayField(TextField(), default=[])

    @classmethod
    def for_request(cls, request):
        return cls.objects.filter(owner=request.user.id).first()


class TenantOwnedMixin(BaseModel):
    tenant = ForeignKey('Tenant', editable=False)
    user_tags = JSONField(default={})

    class Meta:
        abstract = True


class ProviderCredential(TenantOwnedMixin):
    provider = ForeignKey('Provider', related_name='credentials')
    shared_identity = TextLineField()
    shared_secret = TextLineField()

    @classmethod
    def default_for_tenant(cls, tenant, provider):
        return cls.objects.get(tenant=tenant, provider=provider)

    @classmethod
    def create_default_for_tenant(cls, tenant, provider):
        cred = cls(tenant=tenant,
                   provider=provider,
                   shared_identity='',
                   shared_secret='')
        cred.save()
        return cred

    @classmethod
    def clone(cls, __source, tenant, **kwargs):
        # Ensure we are never copying secrets between tenants.
        if tenant == __source.tenant:
            return __source

        # look for creds matching provider
        t_creds = cls.objects.filter(provider=__source.provider)
        if t_creds:
            return t_creds.first()

        # new stub creds for same provider
        return super(ProviderCredential, cls).clone(
            __source,
            name=__source.provider.name,
            tenant=tenant,
            shared_identity='',
            shared_secret='',
            **kwargs)

# Cluster


class Cluster(TenantOwnedMixin):
    P_DESIGN = 'D'
    P_REQUESTED = 'R'
    P_PROVISIONED = 'P'
    P_HISTORICAL = 'H'
    P_TEMPLATE = 'T'

    provision_state = CharField(max_length=1, choices=[
        (P_DESIGN, 'Design'),
        (P_REQUESTED, 'Requested'),
        (P_PROVISIONED, 'Provisioned'),
        (P_HISTORICAL, 'Historical'),
        (P_TEMPLATE, 'Template')
    ], default=P_DESIGN)
    parent_cluster = ForeignKey('Cluster',
                                null=True,
                                editable=False,
                                related_name='children')

    @classmethod
    def clone(cls, __source, name, tenant, **kwargs):
        new_cluster = super(Cluster, cls).clone(__source,
                                                tenant=tenant,
                                                name=name,
                                                provision_state=cls.P_DESIGN,
                                                parent_cluster=None,
                                                **kwargs)

        link_map = {}
        role_map = {}

        for vpc in __source.vpc_set.all():
            vpc.__class__.clone(vpc,
                                cluster=new_cluster,
                                link_map=link_map,
                                role_map=role_map,
                                **kwargs)

        # set client role for new links to new roles corresponding to source
        for (source_link_uuid, new_link) in link_map.iteritems():
            source_link = RoleLink.objects.get(uuid=source_link_uuid)
            old_server_role = source_link.server_role
            new_link.server_role = role_map[old_server_role.uuid]
            new_link.save()

        return new_cluster


class VPC(TenantOwnedMixin):
    cluster = OwnerKey('Cluster')
    provider = ForeignKey('Provider', related_name='vpcs')

    @classmethod
    def clone(cls, __source, cluster, **kwargs):
        new_vpc = super(VPC, cls).clone(__source,
                                        tenant=cluster.tenant,
                                        cluster=cluster,
                                        **kwargs)

        for subnet in __source.subnets.all():
            subnet.__class__.clone(subnet, vpc=new_vpc, cluster=cluster,
                                   **kwargs)

        return new_vpc


class Subnet(TenantOwnedMixin):
    cluster = OwnerKey('Cluster', related_name='subnets')
    zone = ForeignKey('Zone', related_name='subnets')
    vpc = ForeignKey('VPC', related_name='subnets')
    credentials = ForeignKey('ProviderCredential', related_name='subnets')
    netmask = TextLineField()

    @classmethod
    def clone(cls, __source, vpc, cluster, **kwargs):
        new_credentials = __source.credentials.__class__.clone(
            __source.credentials,
            tenant=cluster.tenant,
            **kwargs)

        new_subnet = super(Subnet, cls).clone(
            __source,
            vpc=vpc,
            zone=__source.zone,
            tenant=cluster.tenant,
            cluster=cluster,
            credentials=new_credentials,
            **kwargs)

        for instance in __source.instances.all():
            instance.__class__.clone(instance, subnet=new_subnet, **kwargs)

        return new_subnet


class Instance(TenantOwnedMixin):
    subnet = OwnerKey('Subnet', related_name='instances')
    instance_type = ForeignKey('InstanceType', related_name='instances')

    hostname = TextLineField()
    domain = TextLineField()

    assign_eip = BooleanField(default=False)

    @property
    def fqdn(self):
        return self.hostname + '.' + self.domain

    @classmethod
    def clone(cls, __source, subnet, **kwargs):
        new_instance = BaseModel.clone(__source,
                                       tenant=subnet.tenant,
                                       subnet=subnet,
                                       instance_type=__source.instance_type,
                                       **kwargs)

        # src_vol.uuid -> new_vol, used to remap VolumeUse.volume.
        vol_map = {}

        for vol in __source.volumes.all():
            new_vol = vol.__class__.clone(vol, instance=new_instance, **kwargs)
            vol_map[vol.uuid] = new_vol

        for role in __source.roles.all():
            role.__class__.clone(role,
                                 instance=new_instance,
                                 vol_map=vol_map,
                                 **kwargs)

        return new_instance


class Role(TenantOwnedMixin):
    instance = OwnerKey('Instance', related_name='roles')

    # Generated with:
    # find -iname config.yml | xargs grep role: | \
    #   sed 's/^.*role://g; s/\s//g; s/,/\n/g' | sort | uniq

    ROLE_TYPES = [
        'adhoc',
        'barman',
        'bdr',
        'control',
        'coordinator',
        'datanode',
        'datanode-replica',
        'gtm',
        'log-server',
        'monitor',
        'openvpn-server',
        'pgbouncer',
        'primary',
        'replica',
        'witness',
    ]

    role_type = TextLineField(choices=[(_c, _c) for _c in ROLE_TYPES],
                              default='adhoc')

    @classmethod
    def clone(cls, __source, instance, vol_map, link_map, role_map, **kwargs):
        new_role = super(Role, cls).clone(__source,
                                          instance=instance,
                                          tenant=instance.tenant,
                                          **kwargs)

        role_map[__source.uuid] = new_role

        for source_link in __source.client_links.all():
            new_link = RoleLink.clone(source_link,
                                      tenant=new_role.tenant,
                                      client_role=new_role,
                                      **kwargs)
            link_map[source_link.uuid] = new_link

        for vol_use in __source.used_volumes.all():
            vol_use.__class__.clone(
                vol_use,
                tenant=new_role.tenant,
                role=new_role,
                volume=vol_map[vol_use.uuid])

        return new_role


class RoleLink(TenantOwnedMixin):
    client_role = OwnerKey('Role', related_name='client_links')
    server_role = ForeignKey('Role', related_name='server_links')

    class Meta:
        unique_together = (('client_role', 'server_role'),)


class Volume(TenantOwnedMixin):
    instance = OwnerKey('Instance', related_name='volumes')
    volume_type = TextLineField()
    volume_size = PositiveIntegerField()
    delete_on_termination = BooleanField(default=True)

    class Meta:
        unique_together = (('instance', 'name'),)


class VolumeUse(TenantOwnedMixin):
    role = OwnerKey('Role', related_name='used_volumes')
    volume = ForeignKey('Volume', related_name='used_by_roles')

    class Meta:
        unique_together = (('role', 'volume'),)
