#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''
'''

from __future__ import unicode_literals, absolute_import, print_function

from django.conf import settings
from django.conf.urls import url, include
from django.http import Http404

from rest_framework import routers

from . import views

router = routers.SimpleRouter()

for view_class in views.ALL_VIEWS:
    router.register(view_class.object_class, view_class)
    print("registered:", view_class)

urlpatterns = router.urls

def unknown_api_endpoint(request):
    raise Http404("Unknown API endpoint")


urlpatterns += [
    url(r'', unknown_api_endpoint, name='unknown-api-endpoint')
]
