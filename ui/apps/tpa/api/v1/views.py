#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''DRF views for all TPA model classes.
'''

from __future__ import absolute_import, print_function, unicode_literals

import logging
import random
import string

from django.db import transaction
from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError

from tpa import models

from . import serializers

logger = logging.getLogger(__name__)


# Generic ModelViewSets for all model classes

ALL_VIEWS = []

# User


class UserInvitationView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        logger.debug("data: %s", request.data)
        ser = serializers.UserInvitationSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(ser.errors)
        data = ser.validated_data

        invites = models.UserInvitation.objects.filter(email=data['email'])

        if invites.exists():
            invites.delete()

        users = models.UserInvitation.objects.filter(email=data['email'])

        if users:
            user = users.first()
            if user.is_active:
                return Response(status=200, data={"user": user.id})

        with transaction.atomic():
            user = get_user_model().objects.create(
                username=data["email"],
                email=data["email"],
                password="".join(random.choice(string.digits)
                                 for i in xrange(10)),
                is_active=False,
                is_staff=False,
                is_superuser=False,
            )

            tenant = models.Tenant.objects.create(
                name=data.get('new_tenant_name', data['email']),
                              owner=user)

            invite = ser.create(data)
            invite.user_id = user.id
            invite.save()

        mail_sent = True

        try:
            # django.contrib.email.send_email(data['email', 'invite.uuid'])
            pass
        except:
            mail_sent = False

        if not mail_sent:
            with transaction.atomic():
                invite.delete()
                user.delete()
                tenant.delete()

            return Response(status=400, data={"error": "email send failure"})

        return Response(status=200, data={"user": user.id})


class UserInviteConfirmationView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = (BasicAuthentication,)

    def get(self, request, uuid):
        '''User has clicked the invite link.
        '''
        invite = models.UserInvitation.objects.get(uuid=uuid)
        return Response(status=200, data={
            "invite": invite.uuid,
            "user": invite.user_id,
        })

    def post(self, request, uuid):
        '''User invited registration form submission.
        '''
        data = request.data
        data['invite'] = uuid
        ser = serializers.UserInvitedRegistrationSerializer(data=data)
        if not ser.is_valid():
            raise ValidationError(ser.errors)

        return Response(status=200, data={"user": user.id})


# Cluster

class ClusterUploadView(APIView):
    permission_classes = (IsAdminUser,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        ser = serializers.ConfigYmlSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(ser.errors);
        cluster = ser.create(ser.validated_data)

        return Response(status=200, data={"cluster": cluster.uuid})


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

        return queryset.filter(tenant_in=user_tenants)


def create_generic_viewset(model_class):
    '''Create and return a ViewSet class for a TPA model class. If the class
    is owned by a tenant, a TenantOwnedViewSet is created. Otherwise,
    a generic ViewSet with customizations is created.
    '''
    model_name = model_class.__name__
    view_class_name = "%s" % model_name

    serializer_class = \
        serializers.NamespaceViewSerializer.create_model_serializer_class(
            model_class)

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
                       '__module__': __name__,
                       })

    return (view_class_name, view_class)


for _cls_name in models.__all__:
    (name, klazz) = create_generic_viewset(getattr(models, _cls_name))
    globals()[name] = klazz
    ALL_VIEWS.append(klazz)
