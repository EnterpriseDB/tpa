#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import os
from argparse import ArgumentParser

from .bdr_always_on import BDR_Always_ON
from .bdr_autoscale import BDR_Autoscale
from .images import Images
from .m1 import M1


class SelectArchitecture:
    """Load Architecture class based on the directory argument."""

    ARCHITECTURES = {
        "BDR-Always-ON": BDR_Always_ON,
        "BDR-Autoscale": BDR_Autoscale,
        "Images": Images,
        "M1": M1,
    }

    def __new__(cls, name, *args, **kwargs):
        """
        Create a new class instance of Architecture type based on name.

        Returns: An instance of the selected class from ARCHITECTURES.

        """
        try:
            return cls.ARCHITECTURES[name](*args, **kwargs)
        except KeyError:
            raise KeyError(f"Unknown architecture: {name}")


def configure(argv, tpa_dir=None):
    """
    Configure an Architecture and set location arguments relative to the architecture.

    This function is intended to be called from a script passing in `sys.argv[1:]`.

    An architecture must have a directory containing Architecture configuration:
      * commands/
      * templates/
      * _metadata/
      * deploy.yml
      * README.md

    This directory needs to exist on the same level as the architectures/lib directory.

    """
    # Function argument `tpa_dir` takes precedence over environment variable
    try:
        tpa_dir = tpa_dir or os.environ.get("TPA_DIR", None)
        lib_dir = os.path.join(tpa_dir, "architectures", "lib")
    except TypeError:
        raise EnvironmentError("TPA_DIR not defined")

    # Partially parse just the architecture argument to feed SelectArchitecture
    arch_parser = ArgumentParser(
        "tpaexec configure", add_help=False, usage="%(prog)s <cluster> -a Architecture"
    )
    arch_parser.add_argument("--architecture", "-a", required=True)
    arch_args, _ = arch_parser.parse_known_args(argv)

    # Set a default architecture directory based on core tpa conventions.
    # We rescue this if the architecture is None so we can still show help
    try:
        arch_dir = os.path.join(tpa_dir, "architectures", arch_args.architecture)
    except TypeError:
        arch_dir = None

    architecture = SelectArchitecture(
        name=arch_args.architecture, directory=arch_dir, lib=lib_dir, argv=argv
    )
    architecture.configure()
    return architecture
