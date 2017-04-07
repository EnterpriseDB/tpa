#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

from __future__ import unicode_literals, absolute_import, print_function

from django.conf.urls import include, url

from django.conf import settings
from django.contrib.staticfiles import views
from django.views.generic.base import RedirectView
from django.contrib import admin


admin.autodiscover()

urlpatterns = []

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]


if 'django_ses' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^admin/django-ses/', include('django_ses.urls'))]


urlpatterns += [
    url(r'^$', RedirectView.as_view(url="/index.html")),
    url(r'^api/', include('tpasite.api.urls', namespace='api')),
    url(r'^admin/', include(admin.site.urls)),
]


# static

PAGES = ["index", "login", "home", "cluster", "user_invite_accept"]
PAGE_MATCH = '|'.join(PAGES)


def rewrite_root_dir_to_html(request, page, rest, *args, **kwargs):
    return views.serve(request, path=page+".html", *args, **kwargs)


urlpatterns += [
    url(r'^(?P<page>'+PAGE_MATCH+')/(?P<rest>.*)$', rewrite_root_dir_to_html),
    url(r'^(?P<path>.*)$', views.serve),
]
