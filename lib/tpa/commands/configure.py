#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

import os
import sys
from argparse import ArgumentParser,ArgumentError

from ..cluster import Cluster
from ..platform import Platform

from ..architectures import all_architectures

from ..exceptions import ConfigureError,UnsupportedArchitectureError


def configure(argv, tpa_dir=None):
    """"""

    # Here we're concerned about three of the many things that could be in argv:
    # the name of the cluster, the name of the architecture (both required), and
    # the name of a platform (optional, but the choices depend on the selected
    # architecture).

    # Function argument `tpa_dir` takes precedence over environment variable
    try:
        tpa_dir = tpa_dir or os.environ.get("TPA_DIR", None)
        lib_dir = os.path.join(tpa_dir, "architectures", "lib")
    except TypeError:
        raise EnvironmentError("TPA_DIR not defined")

    p = ArgumentParser(
        "tpaexec configure",
        usage="%(prog)s <cluster name> --architecture Architecture --platform Platform [--help]",
        add_help=False,
    )

    p.add_argument(
        "--architecture", "-a", required=True, choices=list(all_architectures.keys())
    )
    p.exit_on_error = False

    try:
        parsed_args, _ = p.parse_known_args(argv)
    except ArgumentError:
        raise UnsupportedArchitectureError


    # to create the Architecture object, we need to determine the cluster
    # directory

    # Set a default architecture directory based on core tpa conventions.
    # We rescue this if the architecture is None so we can still show help
    try:
        arch_dir = os.path.join(tpa_dir, "architectures", parsed_args.architecture)
    except TypeError:
        arch_dir = None

    arch = all_architectures[parsed_args.architecture](
        directory=arch_dir,
        lib=lib_dir,
        argv=argv)

    # The architecture gets to decide which platforms are supported, so we
    # reparse the options once we know what the available choices are.

    p.exit_on_error = True
    p.add_argument(
        "--platform",
        required=False,
        default=arch.default_platform(),
        choices=arch.supported_platforms(),
    )

    parsed_args, _ = p.parse_known_args(argv)

    platform = Platform.load(parsed_args.platform, arch)

    arch.platform = platform
    arch.validate_arguments(arch.args, platform)

    cluster_dir = arch.args.get("cluster")
    cluster = Cluster(
        cluster_name=os.path.basename(cluster_dir),
        architecture=arch.name,
        platform=platform.name,
    )

    try:
        arch.configure(cluster_dir=cluster_dir, cluster=cluster, platform=platform)
    except ConfigureError as e:
        print(e)
        sys.exit(1)



    # the cluster object is now complete and we can write it
    yaml_configuration = cluster.to_yaml()

    try:
        os.makedirs(cluster_dir)
        config_path = f"{cluster_dir}/config.yml"
        if not os.path.exists(config_path):
            with open(config_path, "w") as cfg:
                cfg.write(yaml_configuration)
    except OSError as e:
        raise ConfigureError(f"Could not write cluster directory: {str(e)}")


    arch.after_configuration(cluster)
