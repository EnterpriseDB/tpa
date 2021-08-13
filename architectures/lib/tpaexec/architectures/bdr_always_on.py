#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

from .bdr import BDR

class BDR_Always_ON(BDR):
    def update_argument_defaults(self, defaults):
        super().update_argument_defaults(defaults)
        defaults.update({
            'barman_volume_size': 128,
            'postgres_volume_size': 64,
            'tpa_2q_repositories': [
                'products/bdr3/release',
                'products/pglogical3/release',
            ]
        })

    def num_instances(self):
        return 10

    def num_locations(self):
        return 2

    def default_location_names(self):
        return ['a', 'b']

    def update_cluster_vars(self, cluster_vars):
        super().update_cluster_vars(cluster_vars)
        cluster_vars.update({
            'extra_postgres_extensions': ['pglogical'],
        })
