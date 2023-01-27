#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.


class Platform:
    """Encapsulates everything we need to know to configure, provision,
    and deploy a Cluster on a particular platform, such as AWS or Docker."""

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        """The name of this platform"""
        return self._name
