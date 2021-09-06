#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

from .bdr import BDR
from typing import List, Tuple

import sys

class BDR_Always_ON(BDR):
    def supported_versions(self) -> List[Tuple[str, str]]:
        return [
            ("11", "3"),
            ("12", "3"),
            ("13", "3"),
            ("12", "4"),
            ("13", "4"),
            ("14", "4"),
        ]

    def update_argument_defaults(self, defaults):
        super().update_argument_defaults(defaults)
        defaults.update(
            {
                "barman_volume_size": 128,
                "postgres_volume_size": 64,
            }
        )

    def num_instances(self):
        return 10

    def num_locations(self):
        return 2

    def default_location_names(self):
        return ["a", "b"]
