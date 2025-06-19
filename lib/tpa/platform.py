#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

import importlib.util

DEFAULT_VOLUME_DEVICE_NAME = "/dev/sd"

from .net import DEFAULT_SUBNET_PREFIX_LENGTH
from .exceptions import PlatformError


class Platform:
    """Encapsulates everything we need to know to configure, provision,
    and deploy a Cluster on a particular platform, such as AWS or Docker."""

    def __init__(self, name, arch):
        self._name = name
        self.arch = arch


    @staticmethod
    def load(name, arch):
        module = "tpa.platforms.%s" % name
        if not importlib.util.find_spec(module):
            raise PlatformError("Unknown platform: %s" % name)

        p = getattr(__import__(module, fromlist=[name]), name)
        return p(name, arch)


    @property
    def name(self):
        """The name of this platform"""
        return self._name

    @staticmethod
    def all_platforms():
        """
        Returns a list of all platform names
        """
        return ["aws", "bare", "docker"]

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

    def setup_local_repo(self):
        """
        Performs necessary platform specific setup for package repository
        """
        pass

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

    def process_arguments(self, args, cluster):
        """
        Makes platform-specific changes to args
        """
        pass

    def argument_defaults(self):
        """
        Make platform-specific changes to argument defaults.
        """
        return {}

    def get_default_subnet_prefix(self, num_instances=None):
        """
        Make platform-specific changes the subnet prefix used if none is specified by the user.
        """
        return DEFAULT_SUBNET_PREFIX_LENGTH

