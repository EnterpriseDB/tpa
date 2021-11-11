#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

from .bdr import BDR
from typing import List, Tuple


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
        # This method must be able to return correct results before the layout
        # templates are loaded, so we hardcode the number of instances defined
        # in the various layouts.
        instances_per_layout = {
            "default": 13,
            "platinum": 13,
            "gold": 11,
            "silver": 6,
            "bronze": 6,
        }
        return instances_per_layout[self.args["layout"] or "default"]

    def default_location_names(self):
        return [chr(ord("a") + i) for i in range(self.num_locations())]

    def update_instances(self, instances):
        """
        Change pgbouncer+haproxy instances in the default layout templates to
        use the 'harp-proxy' role instead when HARP is enabled.
        """
        super().update_instances(instances)
        harp_enabled = self.args.get("failover_manager") == "harp"
        for ins in instances:
            role = ins.get("role")
            if harp_enabled and "pgbouncer" in role and "haproxy" in role:
                ins["role"].append("harp-proxy")
                ins["role"].remove("pgbouncer")
                ins["role"].remove("haproxy")
                if "haproxy_backend_servers" in ins.get("vars", {}):
                    del(ins["vars"]["haproxy_backend_servers"])
                    if not ins["vars"]:
                        del(ins["vars"])
