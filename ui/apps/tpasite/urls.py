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


def rewrite_static_object(request, page, uuid, rest, *args, **kwargs):
    new_static_path = "{0}.html".format(page)
    request.query_params[page] = uuid
    return views.serve(request, path=new_static_path, *args, **kwargs)

def rewrite_static_list(request, page, rest, *args, **kwargs):
    new_static_path = "{0}.html".format(page)
    return views.serve(request, path=new_static_path, *args, **kwargs)

PAGES = '''
    index home cluster user_accept_invite login
'''.strip().split();

PAGE_MATCH = '|'.join(PAGES)

urlpatterns += [
    url(r'^(?P<page>'+PAGE_MATCH+')/(?P<uuid>[a-z0-9+])/(?P<rest>.*)$',
        rewrite_static_object),
    url(r'^(?P<page>'+PAGE_MATCH+')/(?P<rest>.*)$', rewrite_static_list),
    url(r'^(?P<path>.*)$', views.serve),
]
