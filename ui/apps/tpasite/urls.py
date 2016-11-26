#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

from __future__ import unicode_literals, absolute_import, print_function

from django.conf.urls import include, url

from django.conf import settings
from django.contrib.staticfiles import views

urlpatterns = [
    url(r'^api/', include('tpasite.api.urls', namespace='api')),
    url(r'^(?P<path>.*)$', views.serve)
]
