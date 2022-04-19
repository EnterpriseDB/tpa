#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

"""Tests for the main architecture module."""
from tpaexec.architecture import Architecture


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


class TestBasicArchitecture:
    def test_args(self):
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
        assert d.args["architecture"] == "basic"
        assert d.args["cluster"] == "lib/tests/config/cluster-basic"
        assert d.args["hostnames"] == ["zero", "one"]
        assert d.args["network"] == "10.33.0.0/24"
