#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

from typing import List, Dict, Any
from argparse import ArgumentParser, Namespace, SUPPRESS
from functools import reduce
from operator import add

from ..transmogrifier import Transmogrifier

from .common import Common
from .bdr4pgd5 import BDR4PGD5
from .repositories import Repositories
from .replace_2q_repositories import Replace2qRepositories


# Transmogrifier classes that represent changes a user can request directly via
# command-line options. (This list omits "Basic", which is always included, so
# that every other class doesn't have to declare it as a dependency.)

selectable_transmogrifiers = [
    BDR4PGD5,
    Repositories,
    Replace2qRepositories,
]


def transmogrifiers_from_args(args: List[str]) -> List[Transmogrifier]:
    """Returns a list of Transmogrifiers that can apply to a Cluster all the
    changes identified by the given command-line args.
    """

    # We take a list of command-line args and construct a list of zero or more
    # explicitly-requested Transmogrifiers. We'll act only on the user's stated
    # intentions, even if some of the Transmogrifiers we decide to skip here are
    # later included anyway as dependencies of the ones we select.

    tlist = []
    for tclass in selectable_transmogrifiers:
        options = tclass.options()
        p = identifying_parser(options)
        parsed_args, _ = p.parse_known_args(args)
        if options_match(options, parsed_args):
            tlist.append(tclass())

    # We now have a list of Transmogrifier objects for some subset of entries in
    # selectable_transmogrifiers, selected based on their relevance to what's in
    # args. We omit entries for any Transmogrifiers that are already declared as
    # dependencies. Dependencies take precedence over objects we created above
    # because they may be initialised with more information than just args.
    #
    # For example, if args contains --edb-repositories, we need the Repositories
    # Transmogrifier to process the value. We would have created a Repositories
    # object above, but we can ignore it if it occurs somewhere in the .required
    # chain of another Transmogrifier—say, because BDR4PGD5 created one with a
    # PGD5-specific default repository list in addition to the values from args.
    # In this case, we treat --edb-repositories as being subsidiary to a request
    # for "--architecture PGD-Always-ON", rather than an independent operation.
    #
    # In general, we'll use a top-level object only if no Transmogrifier of the
    # same class is better-placed to take ownership of its command-line options.

    dependencies = reduce(add, [t.all_required() for t in tlist], [])
    dependency_classes = set([type(t) for t in dependencies])
    tlist = [t for t in tlist if type(t) not in dependency_classes]

    # If tlist end up empty at this point, we return the empty list since no
    # Transmogrifiers matched (probably `cluster` was the only argument given)
    # we don't want to add Common, the command should error out with `Nothing
    # to do` message.

    if len(tlist) == 0:
        return tlist

    # Next, we build a complete parser for the list of Transmogrifiers, parse
    # the args, and make the results available to all of the Transmogrifiers.
    # We include Common as the first Transmogrifier, because everything else
    # depends on it.

    tlist = [Common(), *tlist]
    p = validating_parser(tlist)
    parsed_args = p.parse_args(args)
    for t in tlist:
        t.set_parsed_args(parsed_args)

    return tlist


def identifying_parser(options: Dict[str, Any]) -> ArgumentParser:
    """Returns an ArgumentParser that recognises only the given options, but
    without any strictures like default values, choices, or 'required' that
    could lead it to raise an error during parsing. It can only be used to
    determine if any of the options were present or not.
    """

    p = ArgumentParser(add_help=False, allow_abbrev=False)
    for optname, optval in options.items():
        option_names = [optname] + optval.get("aliases", [])

        # We can use "store_true" to detect the presence of an option, but for
        # options that specify choices, we use "store" because we want to match
        # against the actual value later.

        omit_keys = ["aliases", "default", "choices", "required", "nargs", "type"]
        kwargs = {k: v for k, v in optval.items() if k not in omit_keys}
        if optval.get("choices"):
            kwargs["action"] = "store"
        else:
            kwargs["action"] = "store_true"

        p.add_argument(*option_names, **kwargs, default=SUPPRESS)

    return p


def options_match(options: Dict[str, Any], parsed_args: Namespace) -> bool:
    """Returns true if the argparse.Namespace parsing results matches the given
    options well enough to identify a Transmogrifier, false otherwise.

    At least one of the given options must be present in the results, and if any
    of the options have choices, the parsed value for it must match one of those
    choices. (Note that we don't check "required" here, so that the validating
    parser can emit sensible error messages about missing options.)
    """

    # If we couldn't parse anything, there's nothing left to check.
    if not vars(parsed_args):
        return False

    # For any options that have choices specified, we must check that the actual
    # value matches one of the choices. This is so that multiple Transmogrifiers
    # can declare the same option with different choices, e.g., BDR4PGD5 wants
    # `--architecture PGD-Always-ON`, but `--architecture Something-Else` might
    # refer to a different class.

    for optname, optval in options.items():
        dest = optval.get("dest", optname.lstrip("-").replace("-", "_"))
        choices = optval.get("choices", [])

        if dest in parsed_args and choices:
            strval = getattr(parsed_args, dest)
            if strval not in choices:
                return False

    return True


def validating_parser(tlist: List[Transmogrifier]) -> ArgumentParser:
    """Returns an ArgumentParser that recognises all of the options for the
    given Transmogrifiers and any others they depends on.
    """

    p = ArgumentParser(allow_abbrev=False)
    seen_classes = set()

    all_transmogrifiers = reduce(add, [[t] + t.all_required() for t in tlist], [])
    for t in all_transmogrifiers:
        if type(t) in seen_classes:
            continue

        for optname, optval in t.options().items():
            option_names = [optname] + optval.get("aliases", [])
            kwargs = {k: v for k, v in optval.items() if k != "aliases"}
            p.add_argument(*option_names, **kwargs)

        seen_classes.add(type(t))

    return p


def add_all_transmogrifier_options(p: ArgumentParser):
    """Add all options recognised by all Transmogrifiers to the given
    ArgumentParser (which already has some options defined), knowing that it
    will be used only to display --help output.
    """

    for t in selectable_transmogrifiers:
        for optname, optval in t.options().items():
            option_names = [optname] + optval.get("aliases", [])
            kwargs = {k: v for k, v in optval.items() if k != "aliases"}
            p.add_argument(*option_names, **kwargs)
