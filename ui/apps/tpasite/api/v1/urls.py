#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

from __future__ import unicode_literals, absolute_import, print_function

from django.conf.urls import include, url

urlpatterns = [
    url(r'^tpa/', include('tpa.api.v1.urls')),
]
