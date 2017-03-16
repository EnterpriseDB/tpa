#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Misc utilities.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def log_trace(logger_):
    def trace_wrapper(fn):
        '''Trace log utility decorator'''
        if not settings.DEBUG:
            return fn

        def trace_call(*args, **kwargs):
            result = None
            logger_.debug("C: %s with args(*%s, **%s)", fn, args, kwargs)

            try:
                result = fn(*args, **kwargs)
            finally:
                logger_.debug("R: %s", result)

            return result

        return trace_call

    return trace_wrapper


if __name__ == '__main__':
    pass

