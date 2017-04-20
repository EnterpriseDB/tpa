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

from rest_framework import generics
from rest_framework.authentication import BasicAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response

from tpa import models
from tpa.generics import create_generic_viewset, TenantOwnedMixin

from . import serializers

logger = logging.getLogger(__name__)

# Generic ModelViewSets for all model classes

ALL_VIEWS = []

# User


class UserInvitationCreateView(generics.CreateAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = serializers.UserInvitationSerializer
    model = models.UserInvitation

    def perform_create(self, serializer):
        data = serializer.validated_data

        invites = models.UserInvitation.objects.filter(email=data['email'])
        users = get_user_model().objects.filter(email=data['email'])

        if invites.exists():
            invites.delete()

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

            invite = serializer.create(data)
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


class UserInvitationRetrieveView(generics.RetrieveAPIView):
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


class UserInvitedRegistrationView(generics.UpdateAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = (BasicAuthentication,)
    serializer_class = serializers.UserInvitedRegistrationSerializer
    queryset = get_user_model().objects

    def post(self, request, uuid):
        '''User invited registration form submission.
        '''
        data = request.data
        invite = models.UserInvitation.objects.get(uuid=uuid)
        user = get_user_model().objects.get(id=invite.user_id)
        data['invite'] = uuid

        ser = serializers.UserInvitedRegistrationSerializer(user, data=data)
        ser._invite = invite
        ser.is_valid(raise_exception=True)
        ser.save()

        return Response(status=200, data={"user": invite.user_id})


# Cluster

class ClusterImportView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        if 'template' in self.request.data:
            return serializers.ClusterFromTemplateSerializer
        return serializers.ConfigYmlSerializer


class ClusterExportView(TenantOwnedMixin, generics.RetrieveAPIView):
    queryset = models.Cluster.objects
    lookup_field = 'uuid'
    serializer_class = serializers.ClusterToYmlSerializer


class InstanceUpdateView(TenantOwnedMixin, generics.UpdateAPIView):
    queryset = models.Instance.objects
    lookup_field = 'uuid'
    serializer_class = serializers.InstanceUpdateSerializer


for _cls_name in models.__all__:
    (name, klazz) = create_generic_viewset(getattr(models, _cls_name))
    globals()[name] = klazz
    ALL_VIEWS.append(klazz)


class TemplateListView(generics.ListAPIView):
    def get_serializer_class(self):
        return Cluster.serializer_class

    def get_queryset(self):
        return models.Cluster.objects.filter(
            provision_state=models.Cluster.P_TEMPLATE)
