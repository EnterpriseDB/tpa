#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''
'''

from __future__ import unicode_literals, absolute_import, print_function

from django.conf.urls import url, include
from django.http import HttpResponseNotFound

from rest_framework_jwt.views import (obtain_jwt_token,
                                      refresh_jwt_token,
                                      verify_jwt_token)

from rest_framework import routers

from . import views


def unknown_api_endpoint(request, *args, **kwargs):
    return HttpResponseNotFound("Unknown API endpoint")


def view_by_method(**view_map):
    default = view_map.get('default')

    def method_selector_view(request, *args, **kwargs):
        method_view = view_map.get(request.method, default)
        if not method_view:
            return HttpResponseNotFound("No handler for this method")
        return method_view(request, *args, **kwargs)

    return method_selector_view


auth_patterns = [
    url(r'^user-invite/$',
        views.UserInvitationCreateView.as_view(), name="user-invite"),
    url(r'^user-invite/(?P<uuid>[a-z0-9-]+)/$',
        views.UserInvitationRetrieveView.as_view(), name="user-invite-detail"),
    url(r'^user/invite/(?P<uuid>[a-z0-9-]+)/$',
        views.UserInvitedRegistrationView.as_view(),
        name="user-registration-invite"),
    url(r'^login/', obtain_jwt_token),
    url(r'^refresh/', refresh_jwt_token),
    url(r'^verify/', verify_jwt_token),
]

urlpatterns = [
    url(r'^auth/', include(auth_patterns)),
    url(r'^cluster/import', views.ClusterImportView.as_view()),
    url(r'^cluster/(?P<uuid>[a-z0-9-]+)/export', views.ClusterExportView.as_view()),
    url(r'^template/', views.TemplateListView.as_view()),
]

router = routers.DefaultRouter()

for view_class in views.ALL_VIEWS:
    router.register(view_class.object_class, view_class)

urlpatterns += router.urls

urlpatterns += [
    url(r'', unknown_api_endpoint, name='unknown-api-endpoint')
]
