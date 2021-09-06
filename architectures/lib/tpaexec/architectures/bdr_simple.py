#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

from .bdr import BDR
from typing import List, Tuple

import sys


class BDR_Simple(BDR):
    def supported_versions(self) -> List[Tuple[str, str]]:
        return [
            ("9.4", "1"),
            ("9.4", "2"),
            ("9.6", "2"),
            ("10", "3"),
            ("11", "3"),
            ("12", "3"),
            ("13", "3"),
            ("12", "4"),
            ("13", "4"),
            ("14", "4"),
        ]

    def add_architecture_options(self, p, g):
        g.add_argument(
            "--num-instances",
            type=int,
            metavar="N",
            help="number of BDR instances required",
            dest="num_instances",
            default=3,
        )
        super().add_architecture_options(p, g)

    def num_locations(self):
        return 1
