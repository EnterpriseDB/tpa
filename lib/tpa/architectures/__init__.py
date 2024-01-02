#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

from .bdr_always_on import BDRAlwaysON
from .pgd_always_on import PGDAlwaysON
from .m1 import M1

all_architectures = {
    "BDR-Always-ON": BDRAlwaysON,
    "PGD-Always-ON": PGDAlwaysON,
    "M1": M1,
}
