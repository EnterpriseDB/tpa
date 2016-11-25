#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''DRF views for all TPA model classes.
'''

from __future__ import unicode_literals, absolute_import, print_function

from rest_framework import serializers, viewsets
from tpa import models
import logging


logger = logging.getLogger(__name__)


# Generic ModelViewSets for all model classes


ALL_VIEWS = []


def create_generic_view(g, model_class):
    model_name = model_class.__name__
    view_class_name = "%s" % model_name

    class Meta:
        model = model_class
        fields = '__all__'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid',
                    'view_name': "api:" + model_name.lower() + "-detail"},
        }

    serializer = type(str("%sSerializer" % model_name),
                      (serializers.HyperlinkedModelSerializer,),
                      {'Meta': Meta,
                       '__module__': __name__,
                       })

    view_class = type(str(view_class_name),
                      (viewsets.ModelViewSet,),
                      {'queryset': model_class.objects.all(),
                       'serializer_class': serializer,
                       'object_class': model_name.lower(),
                       'lookup_field': 'uuid',
                       '__module__': __name__,
                      })

    g[view_class_name] = view_class
    g[serializer.__name__] = serializer
    ALL_VIEWS.append(view_class)


for _cls_name in models.__all__:
    create_generic_view(globals(), getattr(models, _cls_name))
