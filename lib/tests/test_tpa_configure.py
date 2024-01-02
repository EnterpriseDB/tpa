#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

import pytest

from tpa.commands.configure import configure
from tpa.architecture import Architecture
from tpa.architectures import all_architectures
from tpa.exceptions import ConfigureError
from tpa.cluster import Cluster


class BasicArchitecture(Architecture):
    """Basic architecture to test configure function"""

    def __init__(self):
        self._name = "Basic"

    @property
    def name(self):
        return self._name

    def default_platform(self):
        return self.supported_platforms("default")

    def supported_platforms(self, platform=None):
        supported = {
            "default": "basic",
            "basic": "basic",
            "aws": "aws",
        }
        if not platform:
            return supported.values()
        elif platform in supported:
            return supported[platform]
        else:
            raise ConfigureError

    def configure(self, cluster, platform):
        """configure function mock up"""
        return cluster


all_architectures.update({"Basic": BasicArchitecture})


class TestConfigure:
    """test suite for configure command"""

    @pytest.mark.parametrize(
        "argv, error, expected",
        [
            (["test", "-a", "Basic"], None, Cluster),
            (["test", "-a", "Other"], SystemExit, Cluster),
        ],
    )
    def test_configure(self, argv, error, expected):
        """test configure command"""
        if error:
            with pytest.raises(error):
                assert configure(argv) == expected
        else:
            assert type(configure(argv)) == expected
            assert configure(argv).platform == "basic"
            assert configure(argv).architecture == "Basic"
