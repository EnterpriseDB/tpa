#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.
import argparse
import copy
import importlib.util

from ..exceptions import PlatformError
from ..platform import Platform
from ..net import DEFAULT_SUBNET_PREFIX_LENGTH


class CloudPlatform(Platform):
    """Platform for cloud providers."""

    @staticmethod
    def update_barman_instance_volume(arch, args, instance):
        """
        Update an instance used for barman.

        Called in cloud platforms: aws

        For barman instances, convert the default postgres_data volume to
        a correctly-sized barman_data one (if there isn't one already).

        """
        roles = instance.roles
        if "barman" in roles:
            instance_defaults = args.get("instance_defaults", {})
            default_volumes = instance_defaults.get("default_volumes", [])
            volumes = instance.get_setting("volumes", [])

            def _get_volume_for(data, key):
                return next(
                    (
                        vol
                        for vol in data
                        if vol.get("vars", {}).get("volume_for", "") == key
                    ),
                    {},
                )

            barman_volume = _get_volume_for(volumes, "barman_data")
            default_barman_volume = _get_volume_for(default_volumes, "barman_data")
            default_postgres_volume = _get_volume_for(default_volumes, "postgres_data")

            if not (barman_volume or default_barman_volume) and default_postgres_volume:
                v = copy.deepcopy(default_postgres_volume)
                v["vars"]["volume_for"] = "barman_data"
                size = arch.args.get("barman_volume_size")
                if size is not None:
                    v["volume_size"] = size
                # instance["volumes"] = volumes + [v]
                instance.set_settings({ "volumes": volumes + [v]})

    @staticmethod
    def set_cluster_rules(args, cluster, settings):
        """
        Generate cluster network security rules for ssh and vpn access.

        Called in cloud platforms: aws

        Args:
            args: argument list
            settings: settings dictionary to update

        """
        cluster_rules = args.get("cluster_rules", [])
        if not cluster_rules and "vpn_network" not in cluster.group.group_vars:
            cluster_rules.append(
                dict(proto="tcp", from_port=22, to_port=22, cidr_ip="0.0.0.0/0")
            )
            for sn in args.get("subnets", []):
                cluster_rules.append(
                    dict(proto="tcp", from_port=0, to_port=65535, cidr_ip=sn)
                )
        if cluster_rules:
            settings["cluster_rules"] = cluster_rules
