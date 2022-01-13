#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from ..architecture import Architecture


class M1(Architecture):
    def add_architecture_options(self, p, g):
        g.add_argument(
            "--num-cascaded-replicas",
            type=int,
            metavar="N",
            help="number of replicas cascaded from first replica",
            dest="cascaded_replicas",
            default=1,
        )

    def num_instances(self):
        return 3 + self.args.get("cascaded_replicas", 1)

    def default_location_names(self):
        return ["main", "dr"]

    def update_cluster_vars(self, cluster_vars):
        cluster_vars.update(
            {
                "vpn_network": "192.168.33.0/24",
            }
        )
