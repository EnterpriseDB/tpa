#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import copy
import sys
import importlib.util

DEFAULT_VOLUME_DEVICE_NAME = "/dev/sd"


class Platform:
    """
    Represents a single platform that can be used to deploy an architecture, and
    knows how to generate the correct configuration for it.
    """

    def __init__(self, name, arch):
        self.name = name
        self.arch = arch

    @staticmethod
    def load(args, arch):
        """
        Returns an object of the desired Platform subclass
        """
        name = Platform.guess_platform(args) or arch.default_platform()
        module = "tpaexec.platform.%s" % name
        if not importlib.util.find_spec(module):
            print("ERROR: unknown platform: %s" % name, file=sys.stderr)
            sys.exit(-1)

        p = getattr(__import__(module, fromlist=[name]), name)
        return p(name, arch)

    @staticmethod
    def guess_platform(args):
        """
        Returns the name of a platform based on any «--platform x» arguments
        found in the given args, or None if no platform was specified
        """
        for i, arg in enumerate(args):
            if i > 0 and args[i - 1] == "--platform":
                return arg
        return None

    @staticmethod
    def all_platforms():
        """
        Returns a list of all platform names
        """
        return ["aws", "bare", "docker", "vagrant"]

    @property
    def default_volume_device_name(self):
        return DEFAULT_VOLUME_DEVICE_NAME

    def add_platform_options(self, p, g):
        """
        Adds platform-specific options to the (relevant group in the) parser
        (subclasses are expected to override this).
        """
        pass

    def validate_arguments(self, args):
        """
        Performs any platform-specific argument validation required.
        """
        pass

    def supported_distributions(self):
        """
        Returns a list of distributions supported by a platform, which may be
        empty if the choices are (i.e., --distribution will accept anything)
        """
        return None

    def default_distribution(self):
        """
        Returns the platform's default distribution, if any.
        """
        return None

    def image(self, label, **kwargs):
        """
        Returns image parameters corresponding to the given label for a platform
        """
        return {}

    def update_cluster_tags(self, cluster_tags, args, **kwargs):
        """
        Makes platform-specific changes to cluster_tags
        """
        pass

    def update_cluster_vars(self, cluster_vars, args, **kwargs):
        """
        Makes platform-specific changes to cluster_vars
        """
        pass

    def update_locations(self, locations, args, **kwargs):
        """
        Makes platform-specific changes to locations
        """
        pass

    def update_instance_defaults(self, instance_defaults, args, **kwargs):
        """
        Makes platform-specific changes to instance_defaults
        """
        pass

    def update_instances(self, instances, args, **kwargs):
        """
        Makes platform-specific changes to instances
        """
        pass

    def process_arguments(self, args):
        """
        Makes platform-specific changes to args
        """
        pass

    def argument_defaults(self):
        """
        Make platform-specific changes to argument defaults.
        """
        return {}


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
        role = instance.get("role", [])
        if "barman" in role:
            instance_defaults = args.get("instance_defaults", {})
            default_volumes = instance_defaults.get("default_volumes", [])
            volumes = instance.get("volumes", [])

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
                instance["volumes"] = volumes + [v]

    @staticmethod
    def set_cluster_rules(args, settings):
        """
        Generate cluster network security rules for ssh and vpn access.

        Called in cloud platforms: aws

        Args:
            args: argument list
            settings: settings dictionary to update

        """
        cluster_rules = args.get("cluster_rules", [])
        if not cluster_rules and "vpn_network" not in args["cluster_vars"]:
            cluster_rules.append(
                dict(proto="tcp", from_port=22, to_port=22, cidr_ip="0.0.0.0/0")
            )
            for sn in args.get("subnets", []):
                cluster_rules.append(
                    dict(proto="tcp", from_port=0, to_port=65535, cidr_ip=sn)
                )
        if cluster_rules:
            settings["cluster_rules"] = cluster_rules
