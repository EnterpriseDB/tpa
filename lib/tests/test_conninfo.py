#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import pytest
from ansible.errors import AnsibleFilterError
import re
from ..filter_plugins.conninfo import (
    parse_conninfo,
    conninfo_string,
    dbname,
    multihost_conninfo,
)


def test_dbname():
    """
    Test that dbname can modify conninfo strings without adding duplicate
    entries to the output.
    """

    c1 = "host=example dbname=postgres user=u1"
    c2 = dbname(c1, "bdrdb", user="u2")
    d3 = parse_conninfo(c2)

    def all_matches(conninfo, s):
        return [i.start() for i in re.finditer(s, conninfo)]

    assert len(all_matches(c2, "user=")) == 1
    assert len(all_matches(c2, "dbname=")) == 1
    assert d3.get("dbname") == "bdrdb"
    assert d3.get("user") == "u2"


def test_multihost_conninfo():
    """
    Test that multihost_conninfo can merge a list of conninfos to produce one,
    and that it rejects input DSNs that differ anywhere other than host/port.
    """

    inputs = [
        "host=one port=5432 user=x",
        "host=two port=5432 user=x",
        "host=three port=5432 user=x",
        "host=four port=5433 user=x",
        "host=five port=5434 user=y",
    ]

    # Different hosts, same port.
    slice = inputs[0:3]
    merged = multihost_conninfo(slice)
    assert parse_conninfo(merged, "host") == ",".join(
        [parse_conninfo(c, "host") for c in slice]
    )
    assert parse_conninfo(merged, "port") == "5432"

    # Now with a different port.
    slice = inputs[0:4]
    merged = multihost_conninfo(slice)
    assert parse_conninfo(merged, "host") == ",".join(
        [parse_conninfo(c, "host") for c in slice]
    )
    assert parse_conninfo(merged, "port") == ",".join(
        [parse_conninfo(c, "port") for c in slice]
    )

    # Now with a different non-host/port connection parameter, which should
    # provoke an error.
    with pytest.raises(AnsibleFilterError):
        merged = multihost_conninfo(inputs)
