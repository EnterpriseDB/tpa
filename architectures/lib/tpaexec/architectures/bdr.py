#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

from __future__ import print_function

from tpaexec.architecture import Architecture

class BDR(Architecture):
    def add_architecture_options(self, p, g):
        g.add_argument(
            '--bdr-node-group', metavar='NAME',
            help='name of BDR node group',
            default='bdrgroup',
        )
        g.add_argument(
            '--bdr-database', metavar='NAME',
            help='name of BDR-enabled database',
            default='bdrdb',
        )

    def cluster_vars_args(self):
        return super(BDR, self).cluster_vars_args() + [
            'bdr_node_group', 'bdr_database'
        ]

    def update_cluster_vars(self, cluster_vars):
        cluster_vars.update({
            'repmgr_failover': 'manual',
            'postgres_coredump_filter': '0xff',
        })
