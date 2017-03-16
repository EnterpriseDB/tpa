#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''DRF views for all TPA model classes.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from rest_framework.views import APIView

from tpa import models
from .serializers import NamespaceViewSerializer, ConfigYmlSerializer

logger = logging.getLogger(__name__)


# Generic ModelViewSets for all model classes

ALL_VIEWS = []


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

    def get_queryset(self):
        queryset = super(TenantOwnedViewSet, self).get_queryset()
        queryset = self.filter_by_tenant(queryset)

        return queryset

    def filter_by_tenant(self, queryset):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return queryset

        # TODO replace with "currently active tenant"
        user_tenants = models.Tenant.objects.filter(owner=user)

        return queryset.filter(tenant_in=user_tenants)


def create_generic_viewset(model_class):
    '''Create and return a ViewSet for a TPA model class. If the class
    is owned by a tenant, a TenantOwnedViewSet is created. Otherwise,
    a generic ViewSet with customizations is created.
    '''
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

    return (view_class_name, view_class)


for _cls_name in models.__all__:
    (name, klazz) = create_generic_viewset(getattr(models, _cls_name))
    globals()[name] = klazz
    ALL_VIEWS.append(klazz)
