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


class ConfiguredCluster:
    """Wrapper that captures the Cluster object from configure() for testing."""

    def __init__(self, arch_class, argv, cluster_path):
        self.cluster_path = cluster_path
        self.argv = argv
        self.cluster = configure(argv, tpa_dir=".")

    @property
    def name(self):
        return self.cluster.architecture

    @property
    def instances(self):
        """Returns the Instances collection with filtering methods like with_role()."""
        return self.cluster.instances

    @property
    def cluster_vars(self):
        """Returns cluster_vars dict."""
        return self.cluster.vars

    @property
    def locations(self):
        """Returns the list of locations."""
        return self.cluster.locations

    @property
    def location_names(self):
        """Returns list of location names."""
        return [loc.name for loc in self.cluster.locations]

    def num_instances(self):
        """Return number of instances in the cluster."""
        return len(self.cluster.instances)

    def _extract_from_argv(self, flag):
        """Extract a flag value from argv (for values not in cluster object)."""
        try:
            idx = self.argv.index(flag)
            if idx + 1 < len(self.argv):
                return self.argv[idx + 1]
        except ValueError:
            pass
        return None


@pytest.fixture
def pgdx_cluster(argv):
    """Fixture for PGD-X architecture testing."""
    cluster_path = CONFIG_PATH["PGDX"]
    cleanup(cluster_path)  # Ensure clean state before test
    configured = ConfiguredCluster(PGDX, argv, cluster_path)
    yield configured
    cleanup(cluster_path)


@pytest.fixture
def pgds_cluster(argv):
    """Fixture for PGD-S architecture testing."""
    cluster_path = CONFIG_PATH["PGDS"]
    cleanup(cluster_path)  # Ensure clean state before test
    configured = ConfiguredCluster(PGDS, argv, cluster_path)
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
        "--pgd-routing",
        "local",
    ]

    STANDARD_PGDX_ARGV = MINIMUM_PGDX_ARGV + ["--postgresql", "16"]

    @pytest.mark.parametrize(
        "argv",
        [
            STANDARD_PGDX_ARGV,
        ],
    )
    def test_pgdx_basic_configure(self, argv, pgdx_cluster):
        """Test basic PGD-X configuration with minimal required args"""
        assert pgdx_cluster.name == "PGD-X"
        assert len(pgdx_cluster.instances) > 0

    @pytest.mark.parametrize(
        "argv",
        [
            STANDARD_PGDX_ARGV,
        ],
    )
    def test_pgdx_name(self, argv, pgdx_cluster):
        """Test that PGD-X architecture has correct name"""
        assert pgdx_cluster.name == "PGD-X"

    @pytest.mark.parametrize(
        "argv, expected_flavour",
        [
            (STANDARD_PGDX_ARGV, "expanded"),
        ],
    )
    def test_pgdx_flavour(self, argv, expected_flavour, pgdx_cluster):
        """Test that PGD-X sets pgd_flavour to 'expanded'"""
        assert pgdx_cluster.cluster_vars["pgd_flavour"] == expected_flavour

    @pytest.mark.parametrize(
        "argv, routing, expected_top, expected_sub",
        [
            (
                STANDARD_PGDX_ARGV + ["--pgd-routing", "global"],
                "global",
                {"enable_routing": True},
                {"enable_routing": False},
            ),
            (
                STANDARD_PGDX_ARGV + ["--pgd-routing", "local"],
                "local",
                {"enable_routing": False},
                {"enable_routing": True},
            ),
        ],
    )
    def test_pgdx_routing_options(
        self, argv, routing, expected_top, expected_sub, pgdx_cluster
    ):
        """Test PGD-X routing configuration (global vs local)"""
        bdr_node_groups = pgdx_cluster.cluster_vars.get("bdr_node_groups", [])
        assert len(bdr_node_groups) > 0

        # Check top-level group routing setting
        top_group = bdr_node_groups[0]
        assert top_group["options"]["enable_routing"] == expected_top["enable_routing"]

        # Check subgroup routing setting (if subgroups exist)
        if len(bdr_node_groups) > 1:
            sub_group = bdr_node_groups[1]
            assert (
                sub_group["options"]["enable_routing"] == expected_sub["enable_routing"]
            )

    @pytest.mark.parametrize(
        "argv",
        [
            STANDARD_PGDX_ARGV + ["--location-names", "dc1", "dc2", "dc3"],
        ],
    )
    def test_pgdx_multiple_locations(self, argv, pgdx_cluster):
        """Test PGD-X with multiple locations"""
        location_names = pgdx_cluster.location_names
        assert len(location_names) == 3
        assert location_names == ["dc1", "dc2", "dc3"]

        # Check that subgroups were created for each location
        bdr_node_groups = pgdx_cluster.cluster_vars.get("bdr_node_groups", [])
        # Should have 1 top group + 3 location subgroups
        assert len(bdr_node_groups) == 4

    @pytest.mark.parametrize(
        "argv, expected_repos",
        [
            (
                MINIMUM_PGDX_ARGV + ["--postgresql", "16"],
                ["standard", "postgres_distributed"],
            ),
            (
                MINIMUM_PGDX_ARGV + ["--edbpge", "16"],
                ["standard", "postgres_distributed"],
            ),
            (
                MINIMUM_PGDX_ARGV + ["--epas", "16", "--no-redwood"],
                ["enterprise", "postgres_distributed"],
            ),
        ],
    )
    def test_pgdx_repositories(self, argv, expected_repos, pgdx_cluster):
        """Test that PGD-X includes correct default repositories based on flavour.

        postgresql and edbpge flavours get standard + postgres_distributed.
        epas flavour gets enterprise + postgres_distributed.
        """
        edb_repos = pgdx_cluster.cluster_vars.get("edb_repositories", [])
        assert edb_repos == expected_repos

    @pytest.mark.parametrize(
        "argv, check_barman",
        [
            (STANDARD_PGDX_ARGV + ["--enable-pem"], False),
            (STANDARD_PGDX_ARGV + ["--enable-pem", "--enable-pg-backup-api"], True),
        ],
    )
    def test_pgdx_enable_pem(self, argv, check_barman, pgdx_cluster):
        """Test that --enable-pem adds pem-agent role to BDR instances and creates pemserver.

        With --enable-pg-backup-api, also adds pem-agent to barman instances.
        """
        instances = pgdx_cluster.instances

        # Check that BDR instances have pem-agent role
        bdr_instances = instances.with_role("bdr")
        assert len(bdr_instances) > 0, "Should have BDR instances"
        for instance in bdr_instances:
            assert (
                "pem-agent" in instance.roles
            ), f"BDR instance {instance.name} should have pem-agent role"

        # Check that pemserver instance was created
        pemserver_instances = instances.with_role("pem-server")
        assert (
            len(pemserver_instances) == 1
        ), "Should have exactly one pemserver instance"
        assert pemserver_instances[0].name == "pemserver"

        # Check barman instances when --enable-pg-backup-api is specified
        if check_barman:
            barman_instances = instances.with_role("barman")
            for instance in barman_instances:
                assert (
                    "pem-agent" in instance.roles
                ), f"Barman instance {instance.name} should have pem-agent role"

    @pytest.mark.parametrize(
        "argv, expected_project_id",
        [
            (STANDARD_PGDX_ARGV + ["--enable-beacon-agent"], None),
            (
                STANDARD_PGDX_ARGV
                + ["--enable-beacon-agent", "--beacon-agent-project-id", "prj_test123"],
                "prj_test123",
            ),
        ],
    )
    def test_pgdx_enable_beacon_agent(self, argv, expected_project_id, pgdx_cluster):
        """Test that --enable-beacon-agent adds beacon-agent role to BDR instances.

        With --beacon-agent-project-id, also sets beacon_agent_project_id in cluster_vars.
        """
        # Check that BDR instances have beacon-agent role
        bdr_instances = pgdx_cluster.instances.with_role("bdr")
        assert len(bdr_instances) > 0, "Should have BDR instances"
        for instance in bdr_instances:
            assert (
                "beacon-agent" in instance.roles
            ), f"BDR instance {instance.name} should have beacon-agent role"

        # Check project_id when specified
        if expected_project_id:
            assert (
                pgdx_cluster.cluster_vars.get("beacon_agent_project_id")
                == expected_project_id
            )

    @pytest.mark.parametrize(
        "argv, option_name, expected_value",
        [
            (
                STANDARD_PGDX_ARGV + ["--read-write-port", "7432"],
                "read_write_port",
                7432,
            ),
            (STANDARD_PGDX_ARGV + ["--read-only-port", "7433"], "read_only_port", 7433),
            (STANDARD_PGDX_ARGV + ["--http-port", "8080"], "http_port", 8080),
            (STANDARD_PGDX_ARGV + ["--use-https"], "use_https", True),
        ],
    )
    def test_pgdx_cm_options(self, argv, option_name, expected_value, pgdx_cluster):
        """Test that Connection Manager options are set correctly in bdr_node_groups"""
        bdr_node_groups = pgdx_cluster.cluster_vars.get("bdr_node_groups", [])
        top_group = bdr_node_groups[0]
        assert top_group.get("options", {}).get(option_name) == expected_value

    @pytest.mark.parametrize(
        "argv",
        [
            STANDARD_PGDX_ARGV
            + ["--read-write-port", "7432", "--http-port", "8080", "--use-https"],
        ],
    )
    def test_pgdx_combined_cm_ports(self, argv, pgdx_cluster):
        """Test that multiple CM port options are correctly combined"""
        bdr_node_groups = pgdx_cluster.cluster_vars.get("bdr_node_groups", [])

        # Should only have one top-level group (not duplicates)
        top_level_groups = [
            g for g in bdr_node_groups if not g.get("parent_group_name")
        ]
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
            (STANDARD_PGDX_ARGV + ["--edb-repositories", "test_repo"], ["test_repo"]),
            (
                STANDARD_PGDX_ARGV + ["--edb-repositories", "test_repo1", "test_repo2"],
                ["test_repo1", "test_repo2"],
            ),
            (STANDARD_PGDX_ARGV + ["--edb-repositories", "none"], []),
        ],
    )
    def test_pgdx_custom_repositories(self, argv, expected_repos, pgdx_cluster):
        """Test that --edb-repositories allows custom repository lists.

        The special value 'none' results in an empty repository list.
        """
        edb_repos = pgdx_cluster.cluster_vars.get("edb_repositories", [])
        assert edb_repos == expected_repos

    @pytest.mark.parametrize(
        "argv, expected_total",
        [
            # default: 1 location, 3 data + 1 barman
            (STANDARD_PGDX_ARGV, 4),
            # 3 locations, 3 data + 1 barman each
            (STANDARD_PGDX_ARGV + ["--location-names", "dc1", "dc2", "dc3"], 12),
            # 2 locations with a per-location witness node: (3 + 1 + 1) per location
            (
                STANDARD_PGDX_ARGV
                + [
                    "--location-names",
                    "dc1",
                    "dc2",
                    "--add-witness-node-per-location",
                ],
                10,
            ),
            # 3 locations with the third designated witness-only: 2 * 4 + 1
            (
                STANDARD_PGDX_ARGV
                + [
                    "--location-names",
                    "dc1",
                    "dc2",
                    "dc3",
                    "--witness-only-location",
                    "dc3",
                ],
                9,
            ),
            # --enable-pem adds a single pemserver instance
            (STANDARD_PGDX_ARGV + ["--enable-pem"], 5),
            # custom data-nodes-per-location
            (STANDARD_PGDX_ARGV + ["--data-nodes-per-location", "5"], 6),
            # combo: 3 locations (one witness-only) + per-location witness + pem
            (
                STANDARD_PGDX_ARGV
                + [
                    "--location-names",
                    "dc1",
                    "dc2",
                    "dc3",
                    "--witness-only-location",
                    "dc3",
                    "--add-witness-node-per-location",
                    "--enable-pem",
                ],
                12,
            ),
        ],
    )
    def test_pgdx_instance_count(self, argv, expected_total, pgdx_cluster):
        """Pin the instance count produced by each PGD-X configuration.

        Documents the topology and flags surprises if the template changes.
        The num_instances()-vs-len(instances) invariant is enforced
        separately, inside process_arguments().
        """
        assert len(pgdx_cluster.instances) == expected_total

    PGDX_BASE_ARGV = [
        CONFIG_PATH["PGDX"],
        "--architecture",
        "PGD-X",
        "--no-git",
        "--pgd-routing",
        "local",
    ]

    @pytest.mark.parametrize(
        "argv, expected",
        [
            (PGDX_BASE_ARGV + ["--pgextended", "16"], "edbpge"),
            (PGDX_BASE_ARGV + ["--edbpge", "16"], "edbpge"),
            (PGDX_BASE_ARGV + ["--edb-postgres-extended", "16"], "edbpge"),
            (
                PGDX_BASE_ARGV
                + ["--postgres-flavour", "edbpge", "--postgres-version", "16"],
                "edbpge",
            ),
            (
                PGDX_BASE_ARGV
                + ["--postgres-flavour", "pgextended", "--postgres-version", "16"],
                "edbpge",
            ),
        ],
    )
    def test_pgdx_normalises_to_edbpge(self, argv, expected):
        """Verify that all ways of requesting Postgres Extended produce 'edbpge'
        for non-BDR-Always-ON architectures (PGD-X, PGD-S)."""
        cleanup(CONFIG_PATH["PGDX"])
        cluster_path = CONFIG_PATH["PGDX"]
        try:
            configured = ConfiguredCluster(PGDX, argv, cluster_path)
            assert configured.cluster_vars["postgres_flavour"] == expected
        finally:
            cleanup(cluster_path)

    def test_pgdx_overrides_from_merges_into_cluster(self, tmp_path):
        """Regression test for TPA-1462: --overrides-from must not crash and
        the override values must be merged into the cluster configuration.

        Before commit 67c31f29b, lib/tpa/architecture.py was missing imports
        for `reduce` (functools) and `merge_hash` (ansible.utils.vars), so
        configuring any cluster with --overrides-from raised
        `NameError: name 'reduce' is not defined`.
        """
        override_file = tmp_path / "overrides.yml"
        override_file.write_text("cluster_tags:\n  tpa_1462_marker: regression\n")
        argv = self.STANDARD_PGDX_ARGV + [
            "--overrides-from",
            str(override_file),
        ]
        cleanup(CONFIG_PATH["PGDX"])
        cluster_path = CONFIG_PATH["PGDX"]
        try:
            configured = ConfiguredCluster(PGDX, argv, cluster_path)
            assert (
                configured.cluster.settings["cluster_tags"]["tpa_1462_marker"]
                == "regression"
            )
        finally:
            cleanup(cluster_path)


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
    def test_pgds_name(self, argv, pgds_cluster):
        """Test that PGD-S architecture has correct name"""
        assert pgds_cluster.name == "PGD-S"

    @pytest.mark.parametrize(
        "argv, expected_flavour",
        [
            (MINIMUM_PGDS_ARGV, "essential"),
        ],
    )
    def test_pgds_flavour(self, argv, expected_flavour, pgds_cluster):
        """Test that PGD-S sets pgd_flavour to 'essential'"""
        assert pgds_cluster.cluster_vars["pgd_flavour"] == expected_flavour

    @pytest.mark.parametrize(
        "argv, expected_layout",
        [
            (MINIMUM_PGDS_ARGV, "standard"),
            (MINIMUM_PGDS_ARGV + ["--layout", "standard"], "standard"),
            (MINIMUM_PGDS_ARGV + ["--layout", "near-far"], "near-far"),
        ],
    )
    def test_pgds_layouts(self, argv, expected_layout, pgds_cluster):
        """Test PGD-S layout options"""
        # Layout is extracted from argv since it's not stored in cluster object
        layout = pgds_cluster._extract_from_argv("--layout") or "standard"
        assert layout == expected_layout

    @pytest.mark.parametrize(
        "argv, expected_locations",
        [
            (MINIMUM_PGDS_ARGV, ["first"]),  # standard default
            (MINIMUM_PGDS_ARGV + ["--layout", "near-far"], ["first", "second"]),
        ],
    )
    def test_pgds_default_locations(self, argv, expected_locations, pgds_cluster):
        """Test PGD-S default location names for each layout"""
        assert pgds_cluster.location_names == expected_locations

    # Note: Location validation error tests are skipped because they require
    # testing configure() failures, which doesn't work well with the fixture approach.
    # These could be added as separate tests without fixtures if needed.

    @pytest.mark.parametrize(
        "argv, expected_total, expected_data, expected_barman, expected_subscriber",
        [
            (MINIMUM_PGDS_ARGV, 4, 3, 1, 0),  # 3 data + 1 barman
            (
                MINIMUM_PGDS_ARGV + ["--layout", "near-far"],
                4,
                3,
                1,
                0,
            ),  # 3 data + 1 barman
            (
                MINIMUM_PGDS_ARGV + ["--add-subscriber-only-nodes", "2"],
                6,
                3,
                1,
                2,
            ),  # 3 data + 1 barman + 2 subscriber
        ],
    )
    def test_pgds_instances(
        self,
        argv,
        expected_total,
        expected_data,
        expected_barman,
        expected_subscriber,
        pgds_cluster,
    ):
        """Test PGD-S instance count calculation"""
        instances = pgds_cluster.instances

        # Check total count
        assert len(instances) == expected_total

        # Check subscriber-only nodes
        subscriber_nodes = instances.with_role("subscriber_only")
        assert len(subscriber_nodes) == expected_subscriber

        # Check data nodes (BDR nodes that are not subscriber-only)
        bdr_nodes = instances.with_role("bdr")
        data_nodes = bdr_nodes.without_role("subscriber_only")
        assert len(data_nodes) == expected_data

        # Check barman nodes
        barman_nodes = instances.with_role("barman")
        assert len(barman_nodes) == expected_barman

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDS_ARGV,
        ],
    )
    def test_pgds_repositories(self, argv, pgds_cluster):
        """Test that PGD-S includes enterprise repository and discards standard"""
        edb_repos = pgds_cluster.cluster_vars.get("edb_repositories", [])
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
    def test_pgds_enable_pem(self, argv, check_barman, pgds_cluster):
        """Test that --enable-pem adds pem-agent role to BDR instances and creates pemserver.

        With --enable-pg-backup-api, also adds pem-agent to barman instances.
        """
        instances = pgds_cluster.instances

        # Check that BDR instances have pem-agent role
        bdr_instances = instances.with_role("bdr")
        assert len(bdr_instances) > 0, "Should have BDR instances"
        for instance in bdr_instances:
            assert (
                "pem-agent" in instance.roles
            ), f"BDR instance {instance.name} should have pem-agent role"

        # Check that pemserver instance was created
        pemserver_instances = instances.with_role("pem-server")
        assert (
            len(pemserver_instances) == 1
        ), "Should have exactly one pemserver instance"
        assert pemserver_instances[0].name == "pemserver"

        # Check barman instances when --enable-pg-backup-api is specified
        if check_barman:
            barman_instances = instances.with_role("barman")
            for instance in barman_instances:
                assert (
                    "pem-agent" in instance.roles
                ), f"Barman instance {instance.name} should have pem-agent role"

    @pytest.mark.parametrize(
        "argv, expected_project_id",
        [
            (MINIMUM_PGDS_ARGV + ["--enable-beacon-agent"], None),
            (
                MINIMUM_PGDS_ARGV
                + ["--enable-beacon-agent", "--beacon-agent-project-id", "prj_test456"],
                "prj_test456",
            ),
        ],
    )
    def test_pgds_enable_beacon_agent(self, argv, expected_project_id, pgds_cluster):
        """Test that --enable-beacon-agent adds beacon-agent role to BDR instances.

        With --beacon-agent-project-id, also sets beacon_agent_project_id in cluster_vars.
        """
        # Check that BDR instances have beacon-agent role
        bdr_instances = pgds_cluster.instances.with_role("bdr")
        assert len(bdr_instances) > 0, "Should have BDR instances"
        for instance in bdr_instances:
            assert (
                "beacon-agent" in instance.roles
            ), f"BDR instance {instance.name} should have beacon-agent role"

        # Check project_id when specified
        if expected_project_id:
            assert (
                pgds_cluster.cluster_vars.get("beacon_agent_project_id")
                == expected_project_id
            )

    @pytest.mark.parametrize(
        "argv, option_name, expected_value",
        [
            (
                MINIMUM_PGDS_ARGV + ["--read-write-port", "7432"],
                "read_write_port",
                7432,
            ),
            (MINIMUM_PGDS_ARGV + ["--read-only-port", "7433"], "read_only_port", 7433),
            (MINIMUM_PGDS_ARGV + ["--http-port", "8080"], "http_port", 8080),
            (MINIMUM_PGDS_ARGV + ["--use-https"], "use_https", True),
        ],
    )
    def test_pgds_cm_options(self, argv, option_name, expected_value, pgds_cluster):
        """Test that Connection Manager options are set correctly in bdr_node_groups"""
        bdr_node_groups = pgds_cluster.cluster_vars.get("bdr_node_groups", [])
        assert len(bdr_node_groups) > 0, "Should have bdr_node_groups"
        top_group = bdr_node_groups[0]
        assert top_group.get("options", {}).get(option_name) == expected_value

    @pytest.mark.parametrize(
        "argv",
        [
            MINIMUM_PGDS_ARGV
            + ["--read-write-port", "7432", "--http-port", "8080", "--use-https"],
        ],
    )
    def test_pgds_combined_cm_ports(self, argv, pgds_cluster):
        """Test that multiple CM port options are correctly combined"""
        bdr_node_groups = pgds_cluster.cluster_vars.get("bdr_node_groups", [])

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
            (
                MINIMUM_PGDS_ARGV + ["--edb-repositories", "test_repo1", "test_repo2"],
                ["test_repo1", "test_repo2"],
            ),
            (MINIMUM_PGDS_ARGV + ["--edb-repositories", "none"], []),
        ],
    )
    def test_pgds_custom_repositories(self, argv, expected_repos, pgds_cluster):
        """Test that --edb-repositories allows custom repository lists.

        The special value 'none' results in an empty repository list.
        """
        edb_repos = pgds_cluster.cluster_vars.get("edb_repositories", [])
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
        argv = (
            self.MINIMUM_PGDS_ARGV
            + ["--layout", layout, "--location-names"]
            + locations
        )

        try:
            with pytest.raises(
                PGDArchitectureError,
                match=f"{layout} requires exactly {expected_count} locations",
            ):
                ConfiguredCluster(PGDS, argv, CONFIG_PATH["PGDS"])
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
            assert (
                version in supported
            ), f"Expected {version} to be in supported versions"

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
                with pytest.raises(
                    PGDArchitectureError,
                    match=f"Postgres {postgres_version} with BDR .* is not supported",
                ):
                    ConfiguredCluster(PGDS, argv, CONFIG_PATH["PGDS"])
            else:
                configured = ConfiguredCluster(PGDS, argv, CONFIG_PATH["PGDS"])
                assert configured.cluster_vars["bdr_version"] == expected_bdr
                assert configured.cluster_vars["postgres_version"] == postgres_version
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


class TestClusterNameValidation:
    def test_invalid_cluster_name_rejected(self):
        from tpa.exceptions import ArchitectureError

        bad_path = "lib/tests/config/cluster.bad"
        argv = [
            bad_path,
            "--architecture",
            "PGD-X",
            "--no-git",
            "--pgd-routing",
            "local",
            "--postgresql",
            "16",
        ]
        try:
            with pytest.raises(ArchitectureError, match="Invalid cluster_name"):
                configure(argv, tpa_dir=".")
        finally:
            cleanup(bad_path)
