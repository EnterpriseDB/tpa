#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import pytest
from tpaexec.password import (
    generate_password,
)


def test_password():
    """
    Test that generate_password can actually generate different passwords of at
    least 32 characters each.
    """
    p1 = generate_password()
    assert len(p1) >= 32

    p2 = generate_password()
    assert len(p2) >= 32
    assert p1 != p2
