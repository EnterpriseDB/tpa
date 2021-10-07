#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

import pytest
from ansible.errors import AnsibleFilterError
from typing import List, Dict, Tuple
from ..filter_plugins.instances import (
    validate_volume_for,
    translate_volume_deployment_defaults,
    find_replica_tablespace_mismatches,
    ensure_publication,
)

# Each entry in this array represents input that validate_volume_for should
# accept (as "vars") without complaint.

valid_volume_for = [
    {},
    {"volume_for": "postgres_data"},
    {"volume_for": "postgres_tablespace", "tablespace_name": "example"},
]


def test_validate_volume_for():
    """
    Test that validate_volume_for accepts valid volume_for values and raises an
    exception for invalid values or valid values with missing required settings.
    """
    d = "/dev/xvda"
    for v in valid_volume_for:
        assert validate_volume_for(d, v) is None
    with pytest.raises(AnsibleFilterError):
        validate_volume_for(d, {"volume_for": "postgres_unknown"})
    with pytest.raises(AnsibleFilterError):
        validate_volume_for(d, {"volume_for": "postgres_tablespace"})


# Each entry in this array is a tuple whose first item represents the input to
# translate_volume_deployment_defaults, and the second item represents the new
# settings we expect (in addition to what we passed in as input) in the output
# from the function.

volume_translation_tests: List[Tuple[Dict[str, str], Dict[str, str]]] = [
    # Leave empty entries alone
    ({}, {}),
    # Leave it alone if there isn't a volume_for
    ({"mountpoint": "/x"}, {}),
    # Translate postgres_data to /opt/postgres; pass through other variables
    # unchanged
    (
        {"volume_for": "postgres_data", "other": "setting"},
        {"mountpoint": "/opt/postgres"},
    ),
    # Explicit mountpoint overrides translation
    (
        {"volume_for": "postgres_data", "mountpoint": "/x"},
        {},
    ),
    # Derive tablespace mountpoint from tablespace_name
    (
        {"volume_for": "postgres_tablespace", "tablespace_name": "first"},
        {"mountpoint": "/opt/postgres/tablespaces/first"},
    ),
    # Set default luks_volume correctly for postgres_data
    (
        {"volume_for": "postgres_data", "encryption": "luks"},
        {"mountpoint": "/opt/postgres", "luks_volume": "postgres"},
    ),
    # Correctly handle luks_volume override
    (
        {"volume_for": "postgres_data", "encryption": "luks", "luks_volume": "example"},
        {"mountpoint": "/opt/postgres"},
    ),
    # Set default luks_volume correctly for postgres_tablespace
    (
        {
            "volume_for": "postgres_tablespace",
            "tablespace_name": "first",
            "encryption": "luks",
        },
        {
            "mountpoint": "/opt/postgres/tablespaces/first",
            "luks_volume": "first",
        },
    ),
    # Set default luks_volume correctly for postgres_tablespace even with an
    # explicit mountpoint setting
    (
        {
            "volume_for": "postgres_tablespace",
            "tablespace_name": "first",
            "encryption": "luks",
            "mountpoint": "/opt/tablespaces/first",
        },
        {"luks_volume": "first"},
    ),
]


def test_translate_volume_deployment_defaults():
    """
    Test that translate_volume_deployment_defaults can correctly translate
    volume_for into a mountpoint if needed.
    """
    for v in volume_translation_tests:
        # have = defaults + v[0]
        # want = have + v[1]
        have = {"device": "/dev/xvda"}
        have.update(v[0])
        want = {}
        want.update(have)
        want.update(v[1])
        assert translate_volume_deployment_defaults(have) == want


# Each tuple in this array contains an array of `instances` to be passed in to
# find_replica_tablespace_mismatches followed by the expected output, a list of
# mismatched replica names.

tablespace_mismatch_tests = [
    ([], []),
    # One primary and one replica with different volume definitions, but both
    # with a volume for a tablespace named "first".
    (
        [
            {
                "Name": "a",
                "role": ["primary"],
                "volumes": [
                    {},
                    {"vars": {"volume_for": "postgres_data"}},
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "first",
                        }
                    },
                ],
            },
            {
                "Name": "b",
                "role": ["replica"],
                "upstream": "a",
                "volumes": [
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "first",
                        }
                    }
                ],
            },
        ],
        [],
    ),
    # One primary with a volume for "first" and a replica with no volumes.
    (
        [
            {
                "Name": "a",
                "role": ["primary"],
                "volumes": [
                    {},
                    {"vars": {"volume_for": "postgres_data"}},
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "first",
                        }
                    },
                ],
            },
            {
                "Name": "b",
                "role": ["replica"],
                "upstream": "a",
            },
        ],
        ["b"],
    ),
    # One primary with a volume for "first" and a replica with a volume for
    # "second".
    (
        [
            {
                "Name": "a",
                "role": ["primary"],
                "volumes": [
                    {},
                    {"vars": {"volume_for": "postgres_data"}},
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "first",
                        }
                    },
                ],
            },
            {
                "Name": "b",
                "role": ["replica"],
                "upstream": "a",
                "volumes": [
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "second",
                        }
                    }
                ],
            },
        ],
        ["b"],
    ),
    # One primary with a volume for "first", and one replica and a cascading
    # replica both with a volume for "second".
    (
        [
            {
                "Name": "a",
                "role": ["primary"],
                "volumes": [
                    {},
                    {"vars": {"volume_for": "postgres_data"}},
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "first",
                        }
                    },
                ],
            },
            {
                "Name": "b",
                "role": ["replica"],
                "upstream": "a",
                "volumes": [
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "second",
                        }
                    }
                ],
            },
            {
                "Name": "c",
                "role": ["replica"],
                "upstream": "b",
                "volumes": [
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "second",
                        }
                    }
                ],
            },
        ],
        ["b"],
    ),
    # One primary with a volume for "first" and one replica also with a volume for
    # "first", and one cascading replica with a volume for "second".
    (
        [
            {
                "Name": "a",
                "role": ["primary"],
                "volumes": [
                    {},
                    {"vars": {"volume_for": "postgres_data"}},
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "first",
                        }
                    },
                ],
            },
            {
                "Name": "b",
                "role": ["replica"],
                "upstream": "a",
                "volumes": [
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "first",
                        }
                    }
                ],
            },
            {
                "Name": "c",
                "role": ["replica"],
                "upstream": "b",
                "volumes": [
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "second",
                        }
                    }
                ],
            },
        ],
        ["c"],
    ),
    # One primary with a volume for "first" and one replica with a volume for
    # "second", and its cascading replica with a volume for "first".
    (
        [
            {
                "Name": "a",
                "role": ["primary"],
                "volumes": [
                    {},
                    {"vars": {"volume_for": "postgres_data"}},
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "first",
                        }
                    },
                ],
            },
            {
                "Name": "b",
                "role": ["replica"],
                "upstream": "a",
                "volumes": [
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "second",
                        }
                    }
                ],
            },
            {
                "Name": "c",
                "role": ["replica"],
                "upstream": "b",
                "volumes": [
                    {
                        "vars": {
                            "volume_for": "postgres_tablespace",
                            "tablespace_name": "first",
                        }
                    }
                ],
            },
        ],
        ["b", "c"],
    ),
]


def test_find_replica_tablespace_mismatches():
    """
    Test that find_replica_tablespace_mismatches can detect replicas with
    different tablespace volumes than their upstream instances.
    """
    for c in tablespace_mismatch_tests:
        assert find_replica_tablespace_mismatches(c[0]) == c[1]


ensure_publication_tests = [
    # Empty publications, should append given entry
    (
        [],
        {
            "type": "bdr",
            "database": "bdr_database",
            "replication_sets": [{"name": "witness-only", "replicate_insert": False}],
        },
        [
            {
                "type": "bdr",
                "database": "bdr_database",
                "replication_sets": [
                    {"name": "witness-only", "replicate_insert": False}
                ],
            }
        ],
    ),
    # Two publications, one matching entry, should append missing repset.
    (
        [
            {
                "type": "bdr",
                "database": "bdr_database",
                "replication_sets": [{"name": "other", "replicate_insert": True}],
            },
            {
                "type": "bdr",
                "database": "other_database",
                "replication_sets": [{"name": "some_repset"}],
            },
        ],
        {
            "type": "bdr",
            "database": "bdr_database",
            "replication_sets": [{"name": "witness-only", "replicate_insert": False}],
        },
        [
            {
                "type": "bdr",
                "database": "bdr_database",
                "replication_sets": [
                    {"name": "other", "replicate_insert": True},
                    {"name": "witness-only", "replicate_insert": False},
                ],
            },
            {
                "type": "bdr",
                "database": "other_database",
                "replication_sets": [{"name": "some_repset"}],
            },
        ],
    ),
    # Two publications, one complete matching entry, should do nothing.
    (
        [
            {
                "type": "bdr",
                "database": "bdr_database",
                "replication_sets": [{"name": "witness-only", "replicate_delete": True}],
            },
            {
                "type": "bdr",
                "database": "other_database",
                "replication_sets": [{"name": "some_repset"}],
            },
        ],
        {
            "type": "bdr",
            "database": "bdr_database",
            "replication_sets": [{"name": "witness-only", "replicate_insert": False}],
        },
        [
            {
                "type": "bdr",
                "database": "bdr_database",
                "replication_sets": [
                    {"name": "witness-only", "replicate_delete": True},
                ],
            },
            {
                "type": "bdr",
                "database": "other_database",
                "replication_sets": [{"name": "some_repset"}],
            },
        ],
    )
]


def test_ensure_publication():
    """
    Test that ensure_publication correctly adds a publication, or modifies an
    existing publication, or leaves a complete configuration alone.
    """
    for c in ensure_publication_tests:
        assert ensure_publication(c[0], c[1]) == c[2]
