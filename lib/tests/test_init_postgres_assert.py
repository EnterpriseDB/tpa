#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""
Regression tests for the pgbouncer/pgd-proxy listen-port checks in
roles/init/tasks/postgres.yml (TPA-787, TPA-810).

Currently only covers the "Check pgd-proxy listen port configuration"
block. This test check the different asserts using Ansible's own conditional
engine.

The conditionals are read from postgres.yml directly, so editing one there
doesn't require touching this file - it'll just show up next time you run
the tests. If a row then fails, check whether it's a regression or expected
before changing anything. Renaming a task will just break the lookup
instead of quietly passing.

"""

from pathlib import Path

import pytest
import yaml
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.conditional import Conditional
from ansible.template import Templar

POSTGRES_TASKS_FILE = Path(__file__).parents[2] / "roles/init/tasks/postgres.yml"
BLOCK_NAME = "Check pgd-proxy listen port configuration"

_loader = DataLoader()


def _load_check_pgd_proxy_listen_port_configuration():
    tasks = yaml.safe_load(POSTGRES_TASKS_FILE.read_text())
    for task in tasks:
        if task.get("name") == BLOCK_NAME:
            return {t["name"]: t for t in task["block"]}, task.get("when", [])
    raise AssertionError(f"{BLOCK_NAME!r} not found in {POSTGRES_TASKS_FILE}")


TASKS, BLOCK_WHEN = _load_check_pgd_proxy_listen_port_configuration()


def _evaluate(conditions, variables):
    """True/False for a `when` or `assert.that` condition list, Ansible-style."""
    templar = Templar(loader=_loader, variables=variables)
    cond = Conditional(loader=_loader)
    cond.when = conditions if isinstance(conditions, list) else [conditions]
    return cond.evaluate_conditional(templar, templar.available_variables)


def _outcome(task_name, variables):
    """"skipped" | "failed" | "ok" for one task, given a variables dict."""
    if not _evaluate(BLOCK_WHEN, variables):
        return "skipped"
    task = TASKS[task_name]
    task_when = task.get("when")
    if task_when is not None and not _evaluate(task_when, variables):
        return "skipped"
    return "ok" if _evaluate(task["assert"]["that"], variables) else "failed"


BASE_VARS = {
    "inventory_hostname": "testhost",
    "role": ["bdr", "pgd-proxy", "pgbouncer"],
    "bdr_package_version": "5.9.0",
    "pgbouncer_port": 6432,
    "pgd_proxy_options": {"listen_port": 6433, "read_listen_port": 6434},
}


def _vars(**overrides):
    return {**BASE_VARS, **overrides}


READ_WRITE_CLASH_TASK = "Fail if pgbouncer and pgd-proxy listen on the same read-write port"
READ_ONLY_CLASH_TASK = "Fail if pgbouncer and pgd-proxy read-only port clash"
LISTEN_PORT_SET_TASK = "Ensure pgd-proxy listen_port is configured before checking for conflicts"
PGBOUNCER_PORT_SET_TASK = "Ensure pgbouncer_port is configured before checking for conflicts"
READ_LISTEN_PORT_REQUIRED_TASK = "Ensure read_listen_port is configured for BDR 5.5 and later"
READ_LISTEN_PORT_UNKNOWN_VERSION_TASK = "Require read_listen_port when the BDR version is unknown"


@pytest.mark.parametrize(
    ("task_name", "overrides", "expected"),
    [
        # Row 1: everything distinct, no collision
        (READ_WRITE_CLASH_TASK, {}, "ok"),
        (READ_ONLY_CLASH_TASK, {}, "ok"),
        # Row 2: read-write port clash
        (
            READ_WRITE_CLASH_TASK,
            {
                "pgbouncer_port": 6432,
                "pgd_proxy_options": {"listen_port": 6432, "read_listen_port": 6434},
            },
            "failed",
        ),
        # Row 3: read-only port clash
        (
            READ_ONLY_CLASH_TASK,
            {
                "pgbouncer_port": 6432,
                "pgd_proxy_options": {"listen_port": 6433, "read_listen_port": 6432},
            },
            "failed",
        ),
        # Row 4: listen_port explicitly null
        (
            LISTEN_PORT_SET_TASK,
            {"pgd_proxy_options": {"listen_port": None, "read_listen_port": 6434}},
            "failed",
        ),
        # Row 5: listen_port absent entirely
        (LISTEN_PORT_SET_TASK, {"pgd_proxy_options": {"read_listen_port": 6434}}, "failed"),
        # Row 6: read_listen_port absent, BDR < 5.5 -> not required
        (
            READ_LISTEN_PORT_REQUIRED_TASK,
            {"pgd_proxy_options": {"listen_port": 6433}, "bdr_package_version": "5.4.0"},
            "skipped",
        ),
        # Row 7: read_listen_port absent, BDR >= 5.5 -> required
        (READ_LISTEN_PORT_REQUIRED_TASK, {"pgd_proxy_options": {"listen_port": 6433}}, "failed"),
        # Row 8: read_listen_port explicitly null, BDR >= 5.5 -> the fixed gap
        (
            READ_LISTEN_PORT_REQUIRED_TASK,
            {"pgd_proxy_options": {"listen_port": 6433, "read_listen_port": None}},
            "failed",
        ),
        # Row 9: read_listen_port null, BDR < 5.5 -> harmless
        (
            READ_LISTEN_PORT_REQUIRED_TASK,
            {
                "pgd_proxy_options": {"listen_port": 6433, "read_listen_port": None},
                "bdr_package_version": "5.4.0",
            },
            "skipped",
        ),
        # Row 10: pgbouncer_port explicitly null
        (PGBOUNCER_PORT_SET_TASK, {"pgbouncer_port": None}, "failed"),
        # Row 11: no pgbouncer role on host -> clash/port-set tasks all skipped
        (READ_WRITE_CLASH_TASK, {"role": ["bdr", "pgd-proxy"]}, "skipped"),
        (PGBOUNCER_PORT_SET_TASK, {"role": ["bdr", "pgd-proxy"]}, "skipped"),
        # Rows 12-15: unknown-version check requires read_listen_port when
        # bdr_package_version can't be parsed as a version (null, empty, or
        # a non-version string) and read_listen_port is missing.
        (
            READ_LISTEN_PORT_UNKNOWN_VERSION_TASK,
            {"pgd_proxy_options": {"listen_port": 6433}, "bdr_package_version": None},
            "failed",
        ),
        (
            READ_LISTEN_PORT_UNKNOWN_VERSION_TASK,
            {"pgd_proxy_options": {"listen_port": 6433}, "bdr_package_version": ""},
            "failed",
        ),
        (
            READ_LISTEN_PORT_UNKNOWN_VERSION_TASK,
            {
                "pgd_proxy_options": {"listen_port": 6433},
                "bdr_package_version": "this-is-a-non-sense-version",
            },
            "failed",
        ),
        # Row 15: unknown version but read_listen_port present -> satisfied
        (
            READ_LISTEN_PORT_UNKNOWN_VERSION_TASK,
            {
                "pgd_proxy_options": {"listen_port": 6433, "read_listen_port": 6434},
                "bdr_package_version": None,
            },
            "ok",
        ),
        # Row 16: version is parseable -> unknown-version check defers to the
        # BDR-5.5 check and is skipped, even with read_listen_port missing.
        (
            READ_LISTEN_PORT_UNKNOWN_VERSION_TASK,
            {"pgd_proxy_options": {"listen_port": 6433}, "bdr_package_version": "5.9.0"},
            "skipped",
        ),
    ],
)
def test_pgd_proxy_listen_port_matrix(task_name, overrides, expected):
    assert _outcome(task_name, _vars(**overrides)) == expected


def test_read_listen_port_required_when_bdr_package_version_absent():
    """When bdr_package_version isn't set, TPA assumes BDR 5.5 or later --
    the same assumption tpaexec configure makes when it generates
    config.yml -- and so requires read_listen_port. The parametrized
    matrix covers null/empty/unparseable values; this covers the key
    being absent entirely, which _vars() can't express via overrides."""
    variables = _vars(pgd_proxy_options={"listen_port": 6433})
    del variables["bdr_package_version"]

    assert _outcome(READ_LISTEN_PORT_UNKNOWN_VERSION_TASK, variables) == "failed"
    # The BDR-5.5 check defers to it and is skipped when the version is unknown.
    assert _outcome(READ_LISTEN_PORT_REQUIRED_TASK, variables) == "skipped"
