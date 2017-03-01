#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''
'''

from __future__ import unicode_literals, absolute_import, print_function

from django.urls import reverse

import logging


logger = logging.getLogger(__name__)

class APITestHelperMixin(AccountTestMixin):
    def _get(self, _view, _uuid, args={}, expect_code=200):
        url = reverse(_view, kwargs={'uuid': _uuid})
        response = self.client.get(url, args, format='json')
        logger.debug("GET %s -> %s => %s", _view, url, response)

        if expect_code is not None:
            self.assertEqual(response.status_code, expect_code)

        return response

    def _post(self, _view, _uuid, args={}, expect_code=201):
        url = reverse(_view, kwargs={'uuid': _uuid})
        response = self.client.post(url, args, format='json')
        logger.debug("POST %s -> %s => %s", _view, url, response)

        if expect_code is not None:
            self.assertEqual(response.status_code, expect_code)

        return response

    def _put(self, _view, _uuid, args={}, expect_code=200):
        url = reverse(_view, kwargs={'uuid': _uuid})
        response = self.client.put(url, args, format='json')
        logger.debug("PUT %s -> %s => %s",
                     _view, url, response)

        if expect_code is not None:
            self.assertEqual(response.status_code, expect_code)

        return response

    def _patch(self, _view, _uuid, args={}, expect_code=None):
        url = reverse(_view, kwargs={'uuid': _uuid})
        response = self.client.patch(url, args, format='json')
        logger.debug("PATCH %s -> %s => %s", _view, url, response)

        if expect_code is not None:
            self.assertEqual(response.status_code, expect_code)

        return response

    def _delete(self, _view, _uuid, args={}, expect_code=None):
        url = reverse(_view, kwargs={'uuid': _uuid})
        response = self.client.delete(url, args, format='json')
        logger.debug("DELETE %s -> %s => %s", _view, url, response)

        if expect_code is not None:
            self.assertEqual(response.status_code, expect_code)

        return response

if __name__ == '__main__':
    pass

