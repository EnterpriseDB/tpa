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
    url(r'^login/', obtain_jwt_token),
    url(r'^refresh/', refresh_jwt_token),
    url(r'^verify/', verify_jwt_token),
    #url(r'^register/$', AuthRegister.as_view()),
]

urlpatterns += [
    url(r'^cluster_upload_yml/', views.ClusterUploadView.as_view()),
    url(r'^auth/', include(auth_patterns)),
    url(r'', unknown_api_endpoint, name='unknown-api-endpoint')
]
