#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

from __future__ import print_function

import sys

class Platform(object):
    def __init__(self, name, arch):
        self.name = name
        self.arch = arch

    # Returns an object of the desired Platform subclass
    @staticmethod
    def load(args, arch):
        name = Platform.guess_platform(args) or arch.default_platform()
        try:
            p = getattr(__import__('tpaexec.platform.%s' % name, fromlist=[name]), name)
        except ImportError as e:
            print('ERROR: unknown platform: %s' % name, file=sys.stderr)
            sys.exit(-1)
        return p(name, arch)

    # Returns the name of a platform based on any «--platform x» arguments found
    # in the given args, or None if no platform specification was found
    @staticmethod
    def guess_platform(args):
        for i, arg in enumerate(args):
            if i > 0 and args[i-1] == '--platform':
                return arg
        return None

    # Returns a list of all platform names
    @staticmethod
    def all_platforms():
        return ['aws', 'bare', 'docker', 'lxd', 'vagrant']

    # Adds platform-specific options to the (relevant group in the) parser
    # (subclasses are expected to override this).
    def add_platform_options(self, p, g):
        pass

    # Returns a list of distributions supported by a platform, which may be
    # empty if the choices are (i.e., --distribution will accept anything)
    def supported_distributions(self):
        return None

    def default_distribution(self):
        return None

    # Returns image parameters corresponding to the given label for a platform
    def image(self, label, **kwargs):
        return {}

    # Makes platform-specific changes to cluster_tags
    def update_cluster_tags(self, cluster_tags, args, **kwargs):
        pass

    # Makes platform-specific changes to cluster_vars
    def update_cluster_vars(self, cluster_vars, args, **kwargs):
        pass

    # Makes platform-specific changes to locations
    def update_locations(self, locations, args, **kwargs):
        pass

    # Makes platform-specific changes to instance_defaults
    def update_instance_defaults(self, instance_defaults, args, **kwargs):
        pass

    # Makes platform-specific changes to instances
    def update_instances(self, instances, args, **kwargs):
        pass

    # Makes platform-specific changes to args
    def process_arguments(self, args):
        pass
