#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""Tests for lib/tpa architecture module (PGD-X and PGD-S)."""
import shutil
import os

import pytest

from tpa.architectures.pgd_x import PGDX
from tpa.architectures.pgd_s import PGDS
from tpa.commands.configure import configure


CONFIG_PATH = {
    "PGDX": "lib/tests/config/cluster-PGDX",
    "PGDS": "lib/tests/config/cluster-PGDS",
}


def cleanup(path):
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass


class ConfiguredArchitecture:
    """Wrapper class that provides access to both the architecture object and config.yml."""

    def __init__(self, arch_class, argv, cluster_path):
        import yaml

        self.cluster_path = cluster_path
        self.argv = argv

        # Run configure which creates the cluster
        configure(argv, tpa_dir=".")

        # Read the generated config.yml
        config_file = os.path.join(cluster_path, "config.yml")
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        # Create architecture instance for accessing methods like bdr_safe_name
        arch_dir_name = "PGD-X" if arch_class == PGDX else "PGD-S"
        self.arch = arch_class(
            directory=f"architectures/{arch_dir_name}",
            lib="architectures/lib",
            argv=argv,
        )

    @property
    def name(self):
        return self.config.get("architecture")

    @property
    def args(self):
        """Provides args-like access to configuration for compatibility."""
        # Extract location names from location objects
        locations = self.config.get("locations", [])
        location_names = [loc.get("Name") for loc in locations if isinstance(loc, dict)]

        return {
            "architecture": self.config.get("architecture"),
            "pgd_routing": self._extract_from_argv("--pgd-routing"),
            "layout": self._extract_from_argv("--layout") or "standard",
            "location_names": location_names,
            "cluster_vars": self.config.get("cluster_vars", {}),
        }

    def _extract_from_argv(self, flag):
        """Extract a flag value from argv."""
        try:
            idx = self.argv.index(flag)
            if idx + 1 < len(self.argv):
                return self.argv[idx + 1]
        except ValueError:
            pass
        return None

    def num_instances(self):
        """Return number of instances in the cluster."""
        return len(self.config.get("instances", []))

    def bdr_safe_name(self, name):
        """Delegate to the actual architecture instance."""
        return self.arch.bdr_safe_name(name)

    def supported_versions(self):
        """Delegate to the actual architecture instance."""
        return self.arch.supported_versions()


@pytest.fixture
def pgdx_architecture(argv):
    """Fixture for PGD-X architecture testing."""
    cluster_path = CONFIG_PATH["PGDX"]
    cleanup(cluster_path)  # Ensure clean state before test
    configured = ConfiguredArchitecture(PGDX, argv, cluster_path)
    yield configured
    cleanup(cluster_path)


@pytest.fixture
def pgds_architecture(argv):
    """Fixture for PGD-S architecture testing."""
    cluster_path = CONFIG_PATH["PGDS"]
    cleanup(cluster_path)  # Ensure clean state before test
    configured = ConfiguredArchitecture(PGDS, argv, cluster_path)
    yield configured
    cleanup(cluster_path)


# @patch.object(Architecture, "expand_template", expand_template)
class TestPGDXArchitecture:
    """Test suite for PGD-X Architecture class"""

    MINIMUM_PGDX_ARGV = [
        CONFIG_PATH["PGDX"],
        "--architecture",
        "PGD-X",
        "--no-git",
        "--postgresql",
        "16",
        "--pgd-routing",
        "local",
    ]

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDX_ARGV,
        ],
    )
    def test_pgdx_basic_configure(self, argv, pgdx_architecture):
        """Test basic PGD-X configuration with minimal required args"""
        assert pgdx_architecture.args["architecture"] == "PGD-X"
        assert "pgd_routing" in pgdx_architecture.args

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDX_ARGV,
        ],
    )
    def test_pgdx_name(self, argv, pgdx_architecture):
        """Test that PGD-X architecture has correct name"""
        assert pgdx_architecture.name == "PGD-X"

    @pytest.mark.parametrize(
        "argv, expected_flavour",
        [
            (MINIMUM_PGDX_ARGV, "expanded"),
        ],
    )
    def test_pgdx_flavour(self, argv, expected_flavour, pgdx_architecture):
        """Test that PGD-X sets pgd_flavour to 'expanded'"""
        assert (
            pgdx_architecture.args["cluster_vars"]["pgd_flavour"] == expected_flavour
        )

    @pytest.mark.parametrize(
        "argv, routing, expected_top, expected_sub",
        [
            (
                MINIMUM_PGDX_ARGV + ["--pgd-routing", "global"],
                "global",
                {"enable_routing": True},
                {"enable_routing": False},
            ),
            (
                MINIMUM_PGDX_ARGV + ["--pgd-routing", "local"],
                "local",
                {"enable_routing": False},
                {"enable_routing": True},
            ),
        ],
    )
    def test_pgdx_routing_options(
        self, argv, routing, expected_top, expected_sub, pgdx_architecture
    ):
        """Test PGD-X routing configuration (global vs local)"""
        bdr_node_groups = pgdx_architecture.args["cluster_vars"].get("bdr_node_groups", [])
        assert len(bdr_node_groups) > 0

        # Check top-level group routing setting
        top_group = bdr_node_groups[0]
        assert top_group["options"]["enable_routing"] == expected_top["enable_routing"]

        # Check subgroup routing setting (if subgroups exist)
        if len(bdr_node_groups) > 1:
            sub_group = bdr_node_groups[1]
            assert sub_group["options"]["enable_routing"] == expected_sub["enable_routing"]

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDX_ARGV + ["--location-names", "dc1", "dc2", "dc3"],
        ],
    )
    def test_pgdx_multiple_locations(self, argv, pgdx_architecture):
        """Test PGD-X with multiple locations"""
        location_names = pgdx_architecture.args["location_names"]
        assert len(location_names) == 3
        assert location_names == ["dc1", "dc2", "dc3"]

        # Check that subgroups were created for each location
        bdr_node_groups = pgdx_architecture.args["cluster_vars"].get("bdr_node_groups", [])
        # Should have 1 top group + 3 location subgroups
        assert len(bdr_node_groups) == 4

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDX_ARGV,
        ],
    )
    def test_pgdx_repositories(self, argv, pgdx_architecture):
        """Test that PGD-X includes postgres_distributed repository"""
        edb_repos = pgdx_architecture.args["cluster_vars"].get("edb_repositories", [])
        assert "postgres_distributed" in edb_repos

    @pytest.mark.parametrize(
        "argv, check_barman",
        [
            (MINIMUM_PGDX_ARGV + ["--enable-pem"], False),
            (MINIMUM_PGDX_ARGV + ["--enable-pem", "--enable-pg-backup-api"], True),
        ],
    )
    def test_pgdx_enable_pem(self, argv, check_barman, pgdx_architecture):
        """Test that --enable-pem adds pem-agent role to BDR instances and creates pemserver.

        With --enable-pg-backup-api, also adds pem-agent to barman instances.
        """
        instances = pgdx_architecture.config.get("instances", [])

        # Check that BDR instances have pem-agent role
        bdr_instances = [i for i in instances if "bdr" in i.get("role", [])]
        assert len(bdr_instances) > 0, "Should have BDR instances"
        for instance in bdr_instances:
            assert "pem-agent" in instance.get("role", []), f"BDR instance {instance.get('Name')} should have pem-agent role"

        # Check that pemserver instance was created
        pemserver_instances = [i for i in instances if "pem-server" in i.get("role", [])]
        assert len(pemserver_instances) == 1, "Should have exactly one pemserver instance"
        assert pemserver_instances[0].get("Name") == "pemserver"

        # Check barman instances when --enable-pg-backup-api is specified
        if check_barman:
            barman_instances = [i for i in instances if "barman" in i.get("role", [])]
            for instance in barman_instances:
                assert "pem-agent" in instance.get("role", []), f"Barman instance {instance.get('Name')} should have pem-agent role"

    @pytest.mark.parametrize(
        "argv, expected_project_id",
        [
            (MINIMUM_PGDX_ARGV + ["--enable-beacon-agent"], None),
            (MINIMUM_PGDX_ARGV + ["--enable-beacon-agent", "--beacon-agent-project-id", "prj_test123"], "prj_test123"),
        ],
    )
    def test_pgdx_enable_beacon_agent(self, argv, expected_project_id, pgdx_architecture):
        """Test that --enable-beacon-agent adds beacon-agent role to BDR instances.

        With --beacon-agent-project-id, also sets beacon_agent_project_id in cluster_vars.
        """
        instances = pgdx_architecture.config.get("instances", [])

        # Check that BDR instances have beacon-agent role
        bdr_instances = [i for i in instances if "bdr" in i.get("role", [])]
        assert len(bdr_instances) > 0, "Should have BDR instances"
        for instance in bdr_instances:
            assert "beacon-agent" in instance.get("role", []), f"BDR instance {instance.get('Name')} should have beacon-agent role"

        # Check project_id when specified
        if expected_project_id:
            cluster_vars = pgdx_architecture.args["cluster_vars"]
            assert cluster_vars.get("beacon_agent_project_id") == expected_project_id

    @pytest.mark.parametrize(
        "argv, option_name, expected_value",
        [
            (MINIMUM_PGDX_ARGV + ["--read-write-port", "7432"], "read_write_port", 7432),
            (MINIMUM_PGDX_ARGV + ["--read-only-port", "7433"], "read_only_port", 7433),
            (MINIMUM_PGDX_ARGV + ["--http-port", "8080"], "http_port", 8080),
            (MINIMUM_PGDX_ARGV + ["--use-https"], "use_https", True),
        ],
    )
    def test_pgdx_cm_options(self, argv, option_name, expected_value, pgdx_architecture):
        """Test that Connection Manager options are set correctly in bdr_node_groups"""
        bdr_node_groups = pgdx_architecture.args["cluster_vars"].get("bdr_node_groups", [])
        top_group = bdr_node_groups[0]
        assert top_group.get("options", {}).get(option_name) == expected_value

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDX_ARGV + ["--read-write-port", "7432", "--http-port", "8080", "--use-https"],
        ],
    )
    def test_pgdx_combined_cm_ports(self, argv, pgdx_architecture):
        """Test that multiple CM port options are correctly combined"""
        bdr_node_groups = pgdx_architecture.args["cluster_vars"].get("bdr_node_groups", [])

        # Should only have one top-level group (not duplicates)
        top_level_groups = [g for g in bdr_node_groups if not g.get("parent_group_name")]
        assert len(top_level_groups) == 1, "Should have exactly one top-level group"

        top_group = top_level_groups[0]
        options = top_group.get("options", {})

        # Check all options are present in the single top-level group
        assert options.get("read_write_port") == 7432
        assert options.get("http_port") == 8080
        assert options.get("use_https") is True
        # Verify enable_routing is still present (wasn't accidentally removed during merge)
        assert "enable_routing" in options

    @pytest.mark.parametrize(
        "argv, expected_repos",
        [
            (MINIMUM_PGDX_ARGV + ["--edb-repositories", "test_repo"], ["test_repo"]),
            (MINIMUM_PGDX_ARGV + ["--edb-repositories", "test_repo1", "test_repo2"], ["test_repo1", "test_repo2"]),
            (MINIMUM_PGDX_ARGV + ["--edb-repositories", "none"], []),
        ],
    )
    def test_pgdx_custom_repositories(self, argv, expected_repos, pgdx_architecture):
        """Test that --edb-repositories allows custom repository lists.

        The special value 'none' results in an empty repository list.
        """
        edb_repos = pgdx_architecture.args["cluster_vars"].get("edb_repositories", [])
        assert edb_repos == expected_repos


# @patch.object(Architecture, "expand_template", expand_template)
class TestPGDSArchitecture:
    """Test suite for PGD-S Architecture class"""

    MINIMUM_PGDS_ARGV = [
        CONFIG_PATH["PGDS"],
        "--architecture",
        "PGD-S",
        "--no-git",
        "--postgresql",
        "16",
    ]

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDS_ARGV,
        ],
    )
    def test_pgds_name(self, argv, pgds_architecture):
        """Test that PGD-S architecture has correct name"""
        assert pgds_architecture.name == "PGD-S"

    @pytest.mark.parametrize(
        "argv, expected_flavour",
        [
            (MINIMUM_PGDS_ARGV, "essential"),
        ],
    )
    def test_pgds_flavour(self, argv, expected_flavour, pgds_architecture):
        """Test that PGD-S sets pgd_flavour to 'essential'"""
        assert (
            pgds_architecture.args["cluster_vars"]["pgd_flavour"] == expected_flavour
        )

    @pytest.mark.parametrize(
        "argv, expected_layout",
        [
            (MINIMUM_PGDS_ARGV, "standard"),
            (MINIMUM_PGDS_ARGV + ["--layout", "standard"], "standard"),
            (MINIMUM_PGDS_ARGV + ["--layout", "near-far"], "near-far"),
        ],
    )
    def test_pgds_layouts(self, argv, expected_layout, pgds_architecture):
        """Test PGD-S layout options"""
        assert pgds_architecture.args["layout"] == expected_layout

    @pytest.mark.parametrize(
        "argv, expected_locations",
        [
            (MINIMUM_PGDS_ARGV, ["first"]),  # standard default
            (MINIMUM_PGDS_ARGV + ["--layout", "near-far"], ["first", "second"]),
        ],
    )
    def test_pgds_default_locations(self, argv, expected_locations, pgds_architecture):
        """Test PGD-S default location names for each layout"""
        assert pgds_architecture.args["location_names"] == expected_locations

    # Note: Location validation error tests are skipped because they require
    # testing configure() failures, which doesn't work well with the fixture approach.
    # These could be added as separate tests without fixtures if needed.

    @pytest.mark.parametrize(
        "argv, expected_instance_count",
        [
            (MINIMUM_PGDS_ARGV, 4),  # 3 data + 1 barman
            (MINIMUM_PGDS_ARGV + ["--layout", "near-far"], 4),  # 3 data + 1 barman
            (MINIMUM_PGDS_ARGV + ["--add-subscriber-only-nodes", "2"], 6),  # 3 data + 1 barman + 2 subscriber
        ],
    )
    def test_pgds_instances(self, argv, expected_instance_count, pgds_architecture):
        """Test PGD-S instance count calculation"""
        assert pgds_architecture.num_instances() == expected_instance_count

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDS_ARGV,
        ],
    )
    def test_pgds_repositories(self, argv, pgds_architecture):
        """Test that PGD-S includes enterprise repository and discards standard"""
        edb_repos = pgds_architecture.args["cluster_vars"].get("edb_repositories", [])
        assert "enterprise" in edb_repos
        # Standard repo should be discarded (replaced with enterprise)
        assert "standard" not in edb_repos

    @pytest.mark.parametrize(
        "argv, check_barman",
        [
            (MINIMUM_PGDS_ARGV + ["--enable-pem"], False),
            (MINIMUM_PGDS_ARGV + ["--enable-pem", "--enable-pg-backup-api"], True),
        ],
    )
    def test_pgds_enable_pem(self, argv, check_barman, pgds_architecture):
        """Test that --enable-pem adds pem-agent role to BDR instances and creates pemserver.

        With --enable-pg-backup-api, also adds pem-agent to barman instances.
        """
        instances = pgds_architecture.config.get("instances", [])

        # Check that BDR instances have pem-agent role
        bdr_instances = [i for i in instances if "bdr" in i.get("role", [])]
        assert len(bdr_instances) > 0, "Should have BDR instances"
        for instance in bdr_instances:
            assert "pem-agent" in instance.get("role", []), f"BDR instance {instance.get('Name')} should have pem-agent role"

        # Check that pemserver instance was created
        pemserver_instances = [i for i in instances if "pem-server" in i.get("role", [])]
        assert len(pemserver_instances) == 1, "Should have exactly one pemserver instance"
        assert pemserver_instances[0].get("Name") == "pemserver"

        # Check barman instances when --enable-pg-backup-api is specified
        if check_barman:
            barman_instances = [i for i in instances if "barman" in i.get("role", [])]
            for instance in barman_instances:
                assert "pem-agent" in instance.get("role", []), f"Barman instance {instance.get('Name')} should have pem-agent role"

    @pytest.mark.parametrize(
        "argv, expected_project_id",
        [
            (MINIMUM_PGDS_ARGV + ["--enable-beacon-agent"], None),
            (MINIMUM_PGDS_ARGV + ["--enable-beacon-agent", "--beacon-agent-project-id", "prj_test456"], "prj_test456"),
        ],
    )
    def test_pgds_enable_beacon_agent(self, argv, expected_project_id, pgds_architecture):
        """Test that --enable-beacon-agent adds beacon-agent role to BDR instances.

        With --beacon-agent-project-id, also sets beacon_agent_project_id in cluster_vars.
        """
        instances = pgds_architecture.config.get("instances", [])

        # Check that BDR instances have beacon-agent role
        bdr_instances = [i for i in instances if "bdr" in i.get("role", [])]
        assert len(bdr_instances) > 0, "Should have BDR instances"
        for instance in bdr_instances:
            assert "beacon-agent" in instance.get("role", []), f"BDR instance {instance.get('Name')} should have beacon-agent role"

        # Check project_id when specified
        if expected_project_id:
            cluster_vars = pgds_architecture.args["cluster_vars"]
            assert cluster_vars.get("beacon_agent_project_id") == expected_project_id

    @pytest.mark.parametrize(
        "argv, option_name, expected_value",
        [
            (MINIMUM_PGDS_ARGV + ["--read-write-port", "7432"], "read_write_port", 7432),
            (MINIMUM_PGDS_ARGV + ["--read-only-port", "7433"], "read_only_port", 7433),
            (MINIMUM_PGDS_ARGV + ["--http-port", "8080"], "http_port", 8080),
            (MINIMUM_PGDS_ARGV + ["--use-https"], "use_https", True),
        ],
    )
    def test_pgds_cm_options(self, argv, option_name, expected_value, pgds_architecture):
        """Test that Connection Manager options are set correctly in bdr_node_groups"""
        bdr_node_groups = pgds_architecture.args["cluster_vars"].get("bdr_node_groups", [])
        assert len(bdr_node_groups) > 0, "Should have bdr_node_groups"
        top_group = bdr_node_groups[0]
        assert top_group.get("options", {}).get(option_name) == expected_value

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDS_ARGV + ["--read-write-port", "7432", "--http-port", "8080", "--use-https"],
        ],
    )
    def test_pgds_combined_cm_ports(self, argv, pgds_architecture):
        """Test that multiple CM port options are correctly combined"""
        bdr_node_groups = pgds_architecture.args["cluster_vars"].get("bdr_node_groups", [])

        # PGD-S doesn't have subgroups, so all entries are top-level or subscriber-only
        # Just verify the options are set correctly
        top_group = bdr_node_groups[0]
        options = top_group.get("options", {})

        # Check all options are present
        assert options.get("read_write_port") == 7432
        assert options.get("http_port") == 8080
        assert options.get("use_https") is True

    @pytest.mark.parametrize(
        "argv, expected_repos",
        [
            (MINIMUM_PGDS_ARGV + ["--edb-repositories", "test_repo"], ["test_repo"]),
            (MINIMUM_PGDS_ARGV + ["--edb-repositories", "test_repo1", "test_repo2"], ["test_repo1", "test_repo2"]),
            (MINIMUM_PGDS_ARGV + ["--edb-repositories", "none"], []),
        ],
    )
    def test_pgds_custom_repositories(self, argv, expected_repos, pgds_architecture):
        """Test that --edb-repositories allows custom repository lists.

        The special value 'none' results in an empty repository list.
        """
        edb_repos = pgds_architecture.args["cluster_vars"].get("edb_repositories", [])
        assert edb_repos == expected_repos

    @pytest.mark.parametrize(
        "layout, locations, expected_count",
        [
            ("standard", ["first", "second"], 1),
            ("near-far", ["first"], 2),
            ("near-far", ["first", "second", "third"], 2),
        ],
    )
    def test_pgds_invalid_location_count(self, layout, locations, expected_count):
        """Test that layouts with wrong number of locations raise errors"""
        from tpa.exceptions import PGDArchitectureError

        cleanup(CONFIG_PATH["PGDS"])  # Ensure clean state before test
        argv = self.MINIMUM_PGDS_ARGV + ["--layout", layout, "--location-names"] + locations

        try:
            with pytest.raises(PGDArchitectureError, match=f"{layout} requires exactly {expected_count} locations"):
                ConfiguredArchitecture(PGDS, argv, CONFIG_PATH["PGDS"])
        finally:
            cleanup(CONFIG_PATH["PGDS"])


# Shared tests for both PGD-X and PGD-S (testing common PGD functionality)
# @patch.object(Architecture, "expand_template", expand_template)
class TestPGDCommon:
    """Test suite for common PGD functionality shared between PGD-X and PGD-S"""

    @pytest.mark.parametrize(
        "argv, architecture_class",
        [
            (
                [
                    CONFIG_PATH["PGDX"],
                    "--architecture",
                    "PGD-X",
                    "--no-git",
                    "--postgresql",
                    "16",
                    "--pgd-routing",
                    "local",
                ],
                PGDX,
            ),
            (
                [
                    CONFIG_PATH["PGDS"],
                    "--architecture",
                    "PGD-S",
                    "--no-git",
                    "--postgresql",
                    "16",
                ],
                PGDS,
            ),
        ],
    )
    def test_supported_versions(self, argv, architecture_class):
        """Test that both architectures support Postgres 14-18 with BDR 6"""
        arch = architecture_class(
            directory=f"architectures/{architecture_class.__name__.replace('PGD', 'PGD-')}",
            lib="architectures/lib",
            argv=argv,
        )

        supported = arch.supported_versions()

        # Should support at least Postgres 14-18 with BDR 6
        # (architectures may report additional versions, but we only check for officially supported ones)
        required_versions = [
            ("14", "6"),
            ("15", "6"),
            ("16", "6"),
            ("17", "6"),
            ("18", "6"),
        ]

        for version in required_versions:
            assert version in supported, f"Expected {version} to be in supported versions"

    @pytest.mark.parametrize(
        "postgres_version, expected_bdr",
        [
            # Valid versions infer BDR 6
            ("14", "6"),
            ("15", "6"),
            ("16", "6"),
            ("17", "6"),
            ("18", "6"),
            # Invalid version raises error
            ("13", None),
        ],
    )
    def test_postgres_version_handling(self, postgres_version, expected_bdr):
        """Test Postgres version handling.

        Valid versions (14-18) should infer BDR version 6.
        Invalid versions (13) should raise PGDArchitectureError.
        """
        from tpa.exceptions import PGDArchitectureError

        cleanup(CONFIG_PATH["PGDS"])
        argv = [
            CONFIG_PATH["PGDS"],
            "--architecture",
            "PGD-S",
            "--no-git",
            "--postgresql",
            postgres_version,
        ]

        try:
            if expected_bdr is None:
                with pytest.raises(PGDArchitectureError, match=f"Postgres {postgres_version} with BDR .* is not supported"):
                    ConfiguredArchitecture(PGDS, argv, CONFIG_PATH["PGDS"])
            else:
                configured = ConfiguredArchitecture(PGDS, argv, CONFIG_PATH["PGDS"])
                assert configured.args["cluster_vars"]["bdr_version"] == expected_bdr
                assert configured.args["cluster_vars"]["postgres_version"] == postgres_version
        finally:
            cleanup(CONFIG_PATH["PGDS"])

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("MyCluster", "mycluster"),
            ("Test_Cluster", "test_cluster"),
            ("test-cluster", "test-cluster"),
            ("Test Cluster!", "test_cluster_"),
            ("UPPERCASE", "uppercase"),
        ],
    )
    def test_bdr_safe_name(self, name, expected):
        """Test bdr_safe_name transformation"""
        arch = PGDX(
            directory="architectures/PGD-X",
            lib="architectures/lib",
            argv=[
                CONFIG_PATH["PGDX"],
                "--architecture",
                "PGD-X",
                "--no-git",
                "--postgresql",
                "16",
                "--pgd-routing",
                "local",
            ],
        )

        assert arch.bdr_safe_name(name) == expected

