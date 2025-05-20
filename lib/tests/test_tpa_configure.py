#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

import pytest

from tpa.commands.configure import configure
from tpa.architecture import Architecture
from tpa.architectures import all_architectures
from tpa.exceptions import ConfigureError, UnsupportedArchitectureError
from tpa.cluster import Cluster
from tpa.platform import Platform


class BasicArchitecture(Architecture):
    """Basic architecture to test configure function"""

    def __init__(self, directory, lib, argv=None):
        super().__init__(directory, lib, argv)
        self._name = "Basic"

    @property
    def name(self):
        return self._name

    def default_platform(self):
        return self.supported_platforms("default")

    def supported_platforms(self, platform=None):
        supported = {
            "default": "docker",
            "basic": "basic",
            "aws": "aws",
        }
        if not platform:
            return supported.values()
        elif platform in supported:
            return supported[platform]
        else:
            raise ConfigureError

    def configure(self, cluster_dir, cluster, platform):
        """configure function mock up"""
        self.cluster_dir = cluster_dir
        self.cluster = cluster
        self.platform = platform
        return cluster

class BasicPlatform(Platform):
    """Basic platform"""
    pass

all_architectures.update({"Basic": BasicArchitecture})


class TestConfigure:
    """test suite for configure command"""

    @pytest.mark.parametrize(
        "argv, error, expected",
        [
            (["test", "-a", "Basic", "--no-git", "--postgresql", "16"], None, Cluster),
            (["test", "-a", "Other"], UnsupportedArchitectureError, Cluster),
        ],
    )
    def test_configure(self, argv, error, expected):
        """test configure command"""

        if error:
            with pytest.raises(error) as excinfo:
                configure(argv, ".")
            assert excinfo.type == error
        else:
            configure(argv, ".")
