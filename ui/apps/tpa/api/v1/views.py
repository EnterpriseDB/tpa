#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''DRF views for all TPA model classes.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.conf import settings
from django.db.models.fields.reverse_related import ManyToOneRel

from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.utils.field_mapping import get_nested_relation_kwargs
from rest_framework.views import APIView

from tpa import models
from .serializers import ConfigYmlSerializer

logger = logging.getLogger(__name__)


# Generic ModelViewSets for all model classes


ALL_VIEWS = []


def log_trace(fn):
    if not settings.DEBUG:
        logger.debug("Skipping log_trace")
        return fn

    def trace_call(*args, **kwargs):
        result = None
        logger.debug("C: %s with args(*%s, **%s)", fn, args, kwargs)

        try:
            result = fn(*args, **kwargs)
        finally:
            logger.debug("R: %s", result)

        return result

    return trace_call


class NamespaceViewSerializer(serializers.HyperlinkedModelSerializer):
    lookup_field = 'uuid'

    @log_trace
    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = \
            super(NamespaceViewSerializer, self).build_relational_field(
                field_name, relation_info)
        if issubclass(field_class, serializers.HyperlinkedRelatedField):
            field_kwargs['view_name'] = "api:" + field_kwargs['view_name']

        return field_class, field_kwargs

    @log_trace
    def build_url_field(self, field_name, model_class):
        field_class, field_kwargs = super(NamespaceViewSerializer, self)\
            .build_url_field(field_name, model_class)

        logger.debug("Default kwargs: %s", field_kwargs)

        if issubclass(field_class, serializers.HyperlinkedRelatedField):
            field_kwargs['view_name'] = "api:" + field_kwargs['view_name']
            field_kwargs['lookup_field'] = 'url'

        logger.debug("url for %s field_kwargs: %s", field_class, field_kwargs)
        return field_class, field_kwargs

    @log_trace
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

        logger.debug("relation_info: %s remote: %s",
                     relation_info, remote_field)

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

    class Meta(object):
        depth = 5

    @classmethod
    def create_model_serializer_class(klazz, model_class, meta={}):
        serializer_class_name = str("%sSerializer" % (model_class.__name__,))
        fields = filter_fields(model_class)
        logger.debug("fields for %s: %s", model_class.__name__, fields)

        meta_fields = {
            'model': model_class,
            'fields': filter_fields(model_class),
            'extra_kwargs': {
                'url': {'lookup_field': 'uuid'}
            }
        }

        meta_fields.update(meta)
        meta = type(str('Meta'), (klazz.Meta,), meta_fields)
        serializer_class = type(serializer_class_name,
                                (klazz,),
                                {'Meta': meta})

        return serializer_class


def filter_fields(model_class):
    # basic fields except hidden + related fields for owned models
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
        all_fields.remove('uuid')

    return tuple(all_fields)


def get_detail_view(model_class):
    return "api:%s-detail" % (model_class.__name__.lower(),)


class ClusterUploadView(APIView):
    permission_classes = (IsAdminUser,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        ser = ConfigYmlSerializer(data=request.data)
        ser.is_valid()
        cluster = ser.create(ser.validated_data)

        return Response(status=200, data={"cluster": cluster.uuid})


class TenantOwnedViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)


def create_generic_view(g, model_class):
    model_name = model_class.__name__
    view_class_name = "%s" % model_name

    serializer_class = \
        NamespaceViewSerializer.create_model_serializer_class(model_class)

    if issubclass(model_class, models.TenantOwnedMixin):
        logger.debug("tenant: %s", model_class)
        view_base = TenantOwnedViewSet
    else:
        logger.debug("not tenant: %s", model_class)
        view_base = viewsets.ModelViewSet

    view_class = type(str(view_class_name),
                      (view_base,),
                      {'queryset': model_class.objects.all(),
                       'serializer_class': serializer_class,
                       'object_class': model_name.lower(),
                       'model': model_class,
                       'lookup_field': 'uuid',
                       '__module__': __name__,
                       })

    g[view_class_name] = view_class
    ALL_VIEWS.append(view_class)


for _cls_name in models.__all__:
    create_generic_view(globals(), getattr(models, _cls_name))
