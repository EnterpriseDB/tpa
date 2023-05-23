#!/usr/bin/env python3

#  © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

import pytest

from patroni_cluster_facts import PatroniCluster, run


@pytest.fixture
def patroni_cluster():
    return PatroniCluster(
        name="cluster",
        config_dir="/etc/patroni",
        patronictl_path="/usr/bin/patronictl",
        locale="C-UTF8",
    )


class TestPatroniClusterFacts:
    def test_run(self, mocker):
        mocked_popen = mocker.patch("patroni_cluster_facts.Popen")
        mocked_popen_instance = mocked_popen.return_value
        mocked_popen_instance.communicate.return_value = (b"Hello World", b"")
        mocked_popen_instance.returncode = 0
        assert run("command") == ("Hello World", "", 0)

    def test_patronictl_not_installed(self, patroni_cluster, mocker):
        mocker.patch("os.path.exists", return_value=False)
        assert (
            patroni_cluster.installed
            == "Path to patronictl does not exist: /usr/bin/patronictl"
        )

    def test_patroni_cluster_installed(self, patroni_cluster, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch(
            "patroni_cluster_facts.run",
            return_value=("patronictl version 1.2.3", "", 0),
        )
        assert patroni_cluster.installed == "1.2.3"

    def test_patroni_cluster_not_installed(self, patroni_cluster, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("patroni_cluster_facts.run", return_value=("", "Errors", 1))
        assert patroni_cluster.installed == "Errors"

    def test_patroni_cluster_initialised(self, patroni_cluster, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch(
            "patroni_cluster_facts.run",
            return_value=('[{"Cluster": "cluster"}]', "", 0),
        )
        assert patroni_cluster.init == "yes"

    def test_patroni_cluster_present(self, patroni_cluster, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch.object(PatroniCluster, "status", [])
        assert patroni_cluster.init == "present"
