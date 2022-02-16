#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import pytest
import re
from ..filter_plugins.conninfo import (
    parse_conninfo,
    conninfo_string,
    dbname,
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
