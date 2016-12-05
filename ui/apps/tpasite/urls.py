#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

from __future__ import unicode_literals, absolute_import, print_function

from django.conf.urls import include, url

from django.conf import settings
from django.contrib.staticfiles import views
from django.views.generic.base import RedirectView

urlpatterns = []

if settings.DEBUG:
    import debug_toolbar
    from django.contrib import admin
    urlpatterns += [
        url(r'^admin/', include(admin.site.urls)),
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

urlpatterns += [
    url(r'^/$', RedirectView.as_view(url="/index.html")),
    url(r'^api/', include('tpasite.api.urls', namespace='api')),
    url(r'^(?P<path>.*)$', views.serve),
]

