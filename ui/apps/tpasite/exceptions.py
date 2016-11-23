#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Exception handling.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def rest_exception_handler(exc, context):
    logger.debug(exc, exc_info=True)
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code
    elif isinstance(exc, ValidationError):
        response = Response({
            'status': 'error',
            'error_code': 'ERR_VALIDATION',
            'message': exc.message
        },
            status=401)

    return response
