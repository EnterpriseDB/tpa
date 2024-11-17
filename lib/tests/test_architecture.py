#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

"""Tests for the main architecture module."""
import shutil
from unittest.mock import patch

import pytest
from ansible.template import Templar

from tpaexec.architecture import Architecture
from tpaexec.architectures import M1, BDR_Always_ON, PGD_Always_ON
from tpaexec.exceptions import ArchitectureError
from tpaexec.platforms import Platform, PlatformError


CONFIG_PATH = {
    "BASIC": "lib/tests/config/cluster-basic",
    "BDR": "lib/tests/config/cluster-BDR",
    "PGD": "lib/tests/config/cluster-PGD",
}


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


def cleanup(path):
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass


@pytest.fixture
def architecture():
    d = BasicArchitecture(
        directory="lib/tests/architectures/basic",
        lib="lib/tests/architectures/lib",
        argv=[
            CONFIG_PATH["BASIC"],
            "--architecture",
            "basic",
            "--network",
            "10.33.0.0/24",
            "--no-git",
            "--postgresql",
            "14",
        ],
    )
    d.configure(force=True)
    yield d
    cleanup(CONFIG_PATH["BASIC"])


class TestBasicArchitecture:
    def test_args(self, architecture):
        assert architecture.args["architecture"] == "basic"
        assert architecture.args["cluster"] == CONFIG_PATH["BASIC"]
        assert architecture.args["hostnames"] == ["zero", "one"]
        assert architecture.args["network"] == "10.33.0.0/24"


class TestPlatform:
    def test_guess_platform(self):
        assert Platform.guess_platform(["--platform", "basic"]) == "basic"

    def test_guess_platform_none(self):
        assert Platform.guess_platform([]) is None

    def test_unknown_platform(self, architecture):
        with pytest.raises(PlatformError):
            Platform.load(["--platform", "basic"], architecture)

    def test_known_platform(self, architecture):
        assert Platform.load(["--platform", "docker"], architecture).name == "docker"

    def test_default_platform(self, architecture):
        assert Platform.load([], architecture).name == architecture.default_platform()


@pytest.fixture
def architecture_bare():
    d = BasicArchitecture(
        directory="lib/tests/architectures/basic",
        lib="lib/tests/architectures/lib",
        argv=[
            CONFIG_PATH["BASIC"],
            "--architecture",
            "basic",
            "--network",
            "10.33.0.0/24",
            "--platform",
            "bare",
            "--no-git",
            "--postgresql",
            "14",
        ],
    )
    d.configure(force=True)
    yield d
    cleanup(CONFIG_PATH["BASIC"])


class TestBarePlatform:
    def test_bare_setup_local_repo(self, architecture_bare):
        """Bare platform has no OS version to detect so local repo creation should return a warning."""
        with pytest.raises(ArchitectureError):
            architecture_bare.setup_local_repo()


@pytest.fixture
def architecture_m1(argv):
    yield M1(
        directory="architectures/M1",
        lib="lib/tests/architectures/lib",
        argv=argv,
    )
    cleanup(CONFIG_PATH["BASIC"])


def extra_jinja_filters():
    """Provides the custom test `empty` to template the config.yml.j2.

    Returns:
        AnsibleEnvironment: Ansible class to manage jinja2 Environment
    """
    from ansible.template import AnsibleEnvironment
    from lib.test_plugins.tests import empty

    env = AnsibleEnvironment()
    env.tests["empty"] = empty
    return env


def expand_template(self, filename, vars, loader=None):
    """
    Takes a template filename and some args and returns the template output
    """
    loader = loader or self.loader()
    templar = Templar(loader=loader, variables=vars)
    templar.environment = extra_jinja_filters()
    template = loader._tpaexec_get_template(filename)
    return templar.do_template(template)


@patch.object(Architecture, "expand_template", expand_template)
class TestM1Architecture:
    ARGS = [
        CONFIG_PATH["BASIC"],
        "--architecture",
        "M1",
        "--network",
        "10.33.0.0/24",
        "--platform",
        "bare",
        "--no-git",
        "--postgresql",
        "14",
    ]

    @pytest.mark.parametrize(
        argnames=("argv", "expected"),
        argvalues=(
            (
                ARGS + ["--failover-manager", "efm"],
                (3, ["zero", "one", "two", "three"]),
            ),
            (
                ARGS + ["--failover-manager", "repmgr"],
                (3, ["zero", "one", "two", "three"]),
            ),
            (
                ARGS + ["--failover-manager", "patroni"],
                (6, ["zero", "one", "two", "three", "four", "five", "six"]),
            ),
        ),
    )
    def test_m1_instances(self, argv, expected, architecture_m1):
        args = architecture_m1.args
        architecture_m1.validate_arguments(args)
        instances = architecture_m1.num_instances()
        assert instances == expected[0]
        hostnames, _, _ = architecture_m1.hostnames(instances)
        assert hostnames == expected[1]

    @pytest.mark.parametrize(
        argnames=("argv", "error", "expected"),
        argvalues=(
            (ARGS + ["--failover-manager", "efm"], None, None),
            (ARGS + ["--enable-repmgr"], None, None),
            (ARGS + ["--enable-patroni"], None, None),
            (ARGS + ["--failover-manager", "efm", "--enable-efm"], SystemExit, None),
        ),
    )
    def test_m1_args_failover_manager(self, argv, error, expected, architecture_m1):
        if error:
            with pytest.raises(error):
                architecture_m1.configure(force=True)
        else:
            assert architecture_m1.configure(force=True) is expected


@pytest.fixture
def bdr_architecture(argv):
    yield BDR_Always_ON(
        directory="architectures/BDR-Always-ON",
        lib="architectures/lib",
        argv=argv,
    )
    cleanup(CONFIG_PATH["BDR"])


@patch.object(Architecture, "expand_template", expand_template)
class TestBDRArchitecture:
    MINIMUM_BDR_ARGV = [
        CONFIG_PATH["BDR"],
        "--architecture",
        "BDR-Always-ON",
        "--no-git",
        "--postgresql",
        "14",
        "--layout",
        "bronze",
        "--harp-consensus-protocol",
        "etcd",
    ]

    @pytest.mark.parametrize(
        "argv, error, expected",
        [
            (MINIMUM_BDR_ARGV, KeyError, None),
            (
                MINIMUM_BDR_ARGV + ["--enable-harp-probes"],
                None,
                {"enable": True},
            ),
            (
                MINIMUM_BDR_ARGV + ["--enable-harp-probes", "http"],
                None,
                {"enable": True},
            ),
            (
                MINIMUM_BDR_ARGV + ["--enable-harp-probes", "https"],
                None,
                {"enable": True, "secure": True},
            ),
        ],
    )
    def test_bdr_probes(self, argv, error, expected, bdr_architecture):
        bdr_architecture.configure(force=True)
        if error is None:
            assert (
                bdr_architecture.args["cluster_vars"]["harp_http_options"] == expected
            )
        else:
            with pytest.raises(error):
                assert bdr_architecture.args["cluster_vars"]["harp_http_options"]


@pytest.fixture
def pgd_architecture(argv):
    yield PGD_Always_ON(
        directory="architectures/PGD-Always-ON",
        lib="architectures/lib",
        argv=argv,
    )
    cleanup(CONFIG_PATH["PGD"])


@patch.object(Architecture, "expand_template", expand_template)
class TestPGDArchitecture:
    MINIMUM_PGD_ARGV = [
        CONFIG_PATH["PGD"],
        "--architecture",
        "PGD-Always-ON",
        "--no-git",
        "--postgresql",
        "14",
        "--pgd-proxy-routing",
        "local",
    ]

    @pytest.mark.parametrize(
        "argv, error, expected",
        [
            (MINIMUM_PGD_ARGV, KeyError, None),
            (
                MINIMUM_PGD_ARGV + ["--enable-pgd-probes"],
                None,
                {"enable": True},
            ),
            (
                MINIMUM_PGD_ARGV + ["--enable-pgd-probes", "http"],
                None,
                {"enable": True},
            ),
            (
                MINIMUM_PGD_ARGV + ["--enable-pgd-probes", "https"],
                None,
                {"enable": True, "secure": True},
            ),
        ],
    )
    def test_pgd_probes(self, argv, error, expected, pgd_architecture):
        pgd_architecture.configure(force=True)
        if error is None:
            assert pgd_architecture.args["cluster_vars"]["pgd_http_options"] == expected
        else:
            with pytest.raises(error):
                pgd_architecture.args["cluster_vars"]["pgd_http_options"]
