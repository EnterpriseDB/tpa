#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

from .bdr_always_on import BDRAlwaysON  # noqa: F401
from .pgd_always_on import PGDAlwaysON  # noqa: F401
from .pgd_s import PGDS
from .pgd_x import PGDX
from .m1 import M1  # noqa: F401

all_architectures = {
    "PGD-S": PGDS,
    "PGD-X": PGDX,
}
