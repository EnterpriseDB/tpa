#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

"""Tests for the main architecture module."""

import pytest

from tpaexec.architecture import Architecture
from tpaexec.platforms import Platform, PlatformError


class BasicArchitecture(Architecture):
    """
    This represents the bare minimum required to instantiate an Architecture,
    and allows us to test Architecture properties (like hostname generation)
    independent of the functionality implemented by "real" subclasses like M1.
    """

    def num_instances(self):
        return 1

    def num_locations(self):
        return 1


class BasicPlatform(Platform):
    pass


@pytest.fixture
def architecture():
    d = BasicArchitecture(
        directory="lib/tests/architectures/basic",
        lib="lib/tests/architectures/lib",
        argv=[
            "lib/tests/config/cluster-basic",
            "--architecture",
            "basic",
            "--network",
            "10.33.0.0/24",
        ],
    )
    d.configure(force=True)
    return d


class TestBasicArchitecture:
    def test_args(self, architecture):
        assert architecture.args["architecture"] == "basic"
        assert architecture.args["cluster"] == "lib/tests/config/cluster-basic"
        assert architecture.args["hostnames"] == ["zero", "one"]
        assert architecture.args["network"] == "10.33.0.0/24"


class TestPlatform:

    def test_guess_platform(self):
        assert Platform.guess_platform(['--platform', 'basic']) == 'basic'

    def test_guess_platform_none(self):
        assert Platform.guess_platform([]) is None

    def test_unknown_platform(self, architecture):
        with pytest.raises(PlatformError):
            Platform.load(['--platform', 'basic'], architecture)

    def test_known_platform(self, architecture):
        assert Platform.load(['--platform', 'docker'], architecture).name == 'docker'

    def test_default_platform(self, architecture):
        assert Platform.load([], architecture).name == architecture.default_platform()
