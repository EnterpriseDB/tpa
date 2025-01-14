#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

import os
from argparse import ArgumentParser

from ..cluster import Cluster
from ..platform import Platform

from ..architectures import all_architectures


def configure(argv):
    """"""

    # Here we're concerned about three of the many things that could be in argv:
    # the name of the cluster, the name of the architecture (both required), and
    # the name of a platform (optional, but the choices depend on the selected
    # architecture).

    p = ArgumentParser(
        "tpaexec configure",
        usage="%(prog)s <cluster name> --architecture Architecture --platform Platform [--help]",
        add_help=False,
    )

    p.add_argument("cluster")
    p.add_argument(
        "--architecture", "-a", required=True, choices=list(all_architectures.keys())
    )

    parsed_args, _ = p.parse_known_args(argv)

    arch = all_architectures[parsed_args.architecture]()

    # The architecture gets to decide which platforms are supported, so we
    # reparse the options once we know what the available choices are.

    p.add_argument(
        "--platform",
        required=False,
        default=arch.default_platform(),
        choices=arch.supported_platforms(),
    )

    parsed_args, _ = p.parse_known_args(argv)

    platform = Platform(parsed_args.platform)

    cluster = Cluster(
        cluster_name=os.path.basename(parsed_args.cluster),
        architecture=arch.name,
        platform=platform.name,
    )

    return arch.configure(cluster, platform)
