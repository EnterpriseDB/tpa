#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import sys, importlib.util


class Platform(object):
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
        return ["aws", "bare", "docker", "lxd", "vagrant"]

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
