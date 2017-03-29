#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''
'''

from __future__ import unicode_literals, absolute_import, print_function

from django.conf import settings
from django.conf.urls import url, include
from django.http import Http404

from rest_framework_jwt.views import (obtain_jwt_token,
                                      refresh_jwt_token,
                                      verify_jwt_token)

from rest_framework import routers

from . import views

router = routers.DefaultRouter()

for view_class in views.ALL_VIEWS:
    router.register(view_class.object_class, view_class)

urlpatterns = router.urls

def unknown_api_endpoint(request):
    raise Http404("Unknown API endpoint")

auth_patterns = [
    url(r'^user-invite/$',
        views.UserInvitationView.as_view(), name="user-invite"),
    url(r'^user-invite/(?P<uuid>[a-z0-9-]+)/$',
        views.UserInviteConfirmationView.as_view(),
        name="user-invite-confirmation"),
    url(r'^login/', obtain_jwt_token),
    url(r'^refresh/', refresh_jwt_token),
    url(r'^verify/', verify_jwt_token),
]

urlpatterns += [
    url(r'^auth/', include(auth_patterns)),
    url(r'^cluster_upload_yml/', views.ClusterUploadView.as_view()),
    url(r'^template/', views.template_list),
    url(r'', unknown_api_endpoint, name='unknown-api-endpoint')
]
