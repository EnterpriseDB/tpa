#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Generic types and operations on models for interfacing with DRF.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.db.models.fields.reverse_related import ManyToOneRel

from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.utils.field_mapping import get_nested_relation_kwargs

from tpa import models
from tpa.utils import log_trace

logger = logging.getLogger(__name__)


def filter_fields(model_class):
    '''Returns basic fields except hidden + related fields for owned models.
    '''
    all_fields = []

    for field in model_class._meta.get_fields():
        if isinstance(field, ManyToOneRel):
            if isinstance(getattr(field, 'remote_field', None),
                          models.OwnerKey):
                if getattr(field, 'related_name', None):
                    all_fields.append(field.related_name)
        else:
            all_fields.append(field.name)

    if 'url' not in all_fields:
        all_fields.insert(0, 'url')

    return tuple(all_fields)


class NamespaceViewSerializer(serializers.HyperlinkedModelSerializer):
    '''Deep serialization of objects.
    '''
    lookup_field = 'uuid'

    class Meta(object):
        depth = 5

    @log_trace(logger)
    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = \
            super(NamespaceViewSerializer, self).build_relational_field(
                field_name, relation_info)
        if issubclass(field_class, serializers.HyperlinkedRelatedField):
            field_kwargs['view_name'] = "api:" + field_kwargs['view_name']

        return field_class, field_kwargs

    @log_trace(logger)
    def build_url_field(self, field_name, model_class):
        field_class, field_kwargs = super(NamespaceViewSerializer, self)\
            .build_url_field(field_name, model_class)

        logger.debug("Default kwargs: %s", field_kwargs)

        if issubclass(field_class, serializers.HyperlinkedRelatedField):
            field_kwargs['view_name'] = "api:" + field_kwargs['view_name']
            field_kwargs['lookup_field'] = 'url'

        logger.debug("url for %s field_kwargs: %s", field_class, field_kwargs)
        return field_class, field_kwargs

    @log_trace(logger)
    def build_nested_field(self, field_name, relation_info, nested_depth):
        """
        Create nested fields for forward and reverse relationships.

        field types:
            foreign key
                owner key
            identity field

        expand if:
            depth > 0
            if one to many fkey:
                expand
            if many to one fkey:

        """
        field_kwargs = get_nested_relation_kwargs(relation_info)

        model_view_name = get_detail_view(relation_info.related_model)
        remote_field = getattr(relation_info.model_field, 'remote_field', None)
        expand_child = False

        if remote_field:
            if isinstance(remote_field, models.OwnerKey):
                expand_child = True
        elif relation_info.to_many:
            expand_child = True

        if expand_child:
            NestedSerializer = \
                NamespaceViewSerializer.create_model_serializer_class(
                    relation_info.related_model,
                    meta={
                        'depth': nested_depth - 1,
                    }
                )
        else:
            class NestedSerializer(serializers.HyperlinkedRelatedField):
                depth = 0

            field_kwargs['view_name'] = model_view_name
            field_kwargs['lookup_field'] = 'uuid'

        return NestedSerializer, field_kwargs

    def get_serializer(self, *args, **kwargs):
        kwargs['model'] = self.model

        return super(NamespaceViewSerializer, self).get_serializer(
            *args, **kwargs)

    @classmethod
    def create_model_serializer_class(cls, model_class, meta=None):
        meta = meta or {}
        serializer_class_name = str("%sSerializer" % (model_class.__name__,))

        meta_fields = {
            'model': model_class,
            'fields': filter_fields(model_class),
            'extra_kwargs': {
                'url': {'lookup_field': 'uuid'}
            }
        }

        meta_fields.update(meta)
        meta = type(str('Meta'), (cls.Meta,), meta_fields)
        serializer_class = type(serializer_class_name,
                                (cls,),
                                {'Meta': meta})

        return serializer_class


def get_detail_view(model_class):
    return "api:%s-detail" % (model_class.__name__.lower(),)


# Generic views

class TenantOwnedViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super(TenantOwnedViewSet, self).get_queryset()
        return self.filter_by_tenant(queryset)

    def filter_by_tenant(self, queryset):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return queryset

        # TODO replace with "currently active tenant"
        user_tenants = models.Tenant.objects.filter(owner=user)

        return queryset.filter(tenant__in=user_tenants)


def create_generic_viewset(model_class):
    '''Create and return a ViewSet class for a TPA model class. If the class
    is owned by a tenant, a TenantOwnedViewSet is created. Otherwise,
    a generic ViewSet with customizations is created.
    '''
    model_name = model_class.__name__
    view_class_name = "%s" % model_name

    serializer_class = \
        NamespaceViewSerializer.create_model_serializer_class(model_class)

    if issubclass(model_class, models.TenantOwnedMixin):
        view_base = TenantOwnedViewSet
    else:
        view_base = viewsets.ModelViewSet

    view_class = type(str(view_class_name),
                      (view_base,),
                      {'queryset': model_class.objects.all(),
                       'serializer_class': serializer_class,
                       'object_class': model_name.lower(),
                       'model': model_class,
                       'lookup_field': 'uuid',
                       '__module__': __name__})

    return (view_class_name, view_class)


if __name__ == '__main__':
    pass
