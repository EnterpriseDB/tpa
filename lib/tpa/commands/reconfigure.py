#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

import os
import shutil
from typing import List
from argparse import ArgumentParser

from tpa.exceptions import ConfigureError

from ..cluster import Cluster
from ..transmogrifier import apply, describe, check
from ..transmogrifiers import transmogrifiers_from_args, add_all_transmogrifier_options


def reconfigure(args: List[str]) -> None:
    """Makes one or more changes to the configuration of an existing cluster."""

    # First, we define a parser that recognises a few top-level options to the
    # reconfigure command, including --help, which is handled specially below.
    # (We add the cluster directory afterwards, because we want --help to work
    # even without it.)

    p = argument_parser(add_help=False)
    p.add_argument("--help", action="store_true")
    add_main_arguments(p)

    # To display useful --help output, we need to specially (re-)construct a
    # parser that recognise all options from all possible Transmogrifiers.

    parsed_args, _ = p.parse_known_args(args)
    if parsed_args.help:
        helper = argument_parser(add_help=True)
        helper.add_argument("cluster", help="existing cluster directory")
        add_main_arguments(helper)
        add_all_transmogrifier_options(helper)
        helper.parse_args(args)

    # Now that we don't need to worry about being helpful, we teach the parser
    # about the required cluster directory argument, re-parse the command line
    # and create a Cluster object from the given directory.

    p.add_argument("cluster")

    parsed_args, remaining_args = p.parse_known_args(args)

    cluster_dir = parsed_args.cluster
    cluster_name = os.path.basename(cluster_dir)

    config_file = os.path.join(cluster_dir, "config.yml")
    if not os.path.exists(config_file):
        raise ConfigureError(f"{config_file} does not exist")

    cluster = Cluster.from_yaml(config_file, cluster_name=cluster_name)

    # Next, parse the remaining command-line arguments to obtain a list of
    # Transmogrifiers; and describe, check, or apply the requested changes.

    tlist = transmogrifiers_from_args(remaining_args)

    if parsed_args.describe_only:
        print(describe(cluster, tlist))
    elif parsed_args.check_only:
        print(check(cluster, tlist))
    else:
        apply(cluster, tlist)

        output_file = os.path.join(cluster_dir, parsed_args.output_file)
        write_output(cluster, output_file)


def argument_parser(**kwargs) -> ArgumentParser:
    return ArgumentParser(
        "tpaexec reconfigure",
        usage="%(prog)s <cluster name> [--describe] [--output <output_file>] …",
        **kwargs,
    )


def add_main_arguments(p: ArgumentParser):
    g = p.add_argument_group("main command options")
    g.add_argument(
        "--describe",
        dest="describe_only",
        action="store_true",
        help="describe what would be changed, without changing anything",
    )
    g.add_argument(
        "--check",
        dest="check_only",
        action="store_true",
        help="validate changes against the cluster, without changing anything",
    )
    g.add_argument(
        "--output",
        dest="output_file",
        default="config.yml",
        help="write generated output (config.yml) to this file",
    )


def write_output(cluster: Cluster, output_file: str) -> None:
    """Writes the given cluster configuration as a new config.yml, while
    ensuring that the original contents are still accessible somehow."""

    # If the cluster directory is already initialised as a Git repository, we
    # don't need to do anything special. Otherwise, if the output file already
    # exists, we make a numbered backup file before overwriting it.
    #
    # XXX Should we run `git status` instead? Do we need to worry about whether
    # output_file is tracked or not?

    if os.path.exists(output_file) and not os.path.exists(
        os.path.join(cluster.name, ".git")
    ):
        counter = 0
        backup_file = output_file
        while os.path.exists(backup_file):
            counter += 1
            backup_file = f"{output_file}.~{counter}~"
        shutil.copyfile(output_file, backup_file)

    with open(output_file, "w") as f:
        f.write(cluster.to_yaml())
