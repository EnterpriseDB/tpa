#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

from typing import Any, Dict, List
from abc import ABC, abstractmethod
from argparse import Namespace
from collections import deque
from functools import reduce
from operator import add

from tpa.cluster import Cluster
from tpa.checkresult import CheckResult
from tpa.changedescription import ChangeDescription
from tpa.exceptions import ConfigureError, TransmogrifierError


class Transmogrifier(ABC):
    """Represents any change to a Cluster in the abstract.

    The best way to think of a Transmogrifier is as a machine that takes some
    user input (e.g., a dial set to eel, giant bug, baboon, or dinosaur) and
    makes some corresponding changes to a Cluster.

    A Transmogrifier can apply() changes to a given Cluster object, or return
    a(n eventually human-readable) description() of the changes it would make.
    This abstract base class defines the Transmogrifier interface. Subclasses
    must implement apply() and other methods.

    Transmogrifiers must declare the options() they require. For details about
    how command-line arguments are parsed, see transmogrifiers_from_args() in
    tpa.transmogrifiers.

    A Transmogrifier may require() other Transmogrifiers to delegate work.
    """

    @classmethod
    def options(cls) -> Dict[str, Dict[str, Any]]:
        """Returns a mapping from the names of options that this class requires
        to the definition of each option, in ArgumentParser.add_argument terms.
        (See the opt() helper function exported below for details.)
        """
        return {}

    def set_parsed_args(self, parsed_args: Namespace):
        """Stores the results of parsing command-line options, passed in by the
        caller. See transmogrifiers_from_args() for details.
        """
        self._args = parsed_args
        for req in self.required:
            req.set_parsed_args(parsed_args)

    @property
    def args(self) -> Namespace:
        """Returns an argparse.Namespace with the results from parsing
        command-line options, as set using set_parsed_args(). All Transmogrifier
        subclasses have access to the same parsed information through self.args.
        See transmogrifiers_from_args() for details.
        """
        return getattr(self, "_args", Namespace())

    def require(self, t: "Transmogrifier"):
        """Records the given Transmogrifier object as a dependency of this one.

        We always apply() the "Common" Transmogrifier before all others, so you
        don't need to require it explicitly anywhere.
        """
        self._requires = self.required + [t]

    @property
    def required(self) -> "List[Transmogrifier]":
        """Returns a list of zero of more other Transmogrifier objects that this
        Transmogrifier directly requires.
        """
        return getattr(self, "_requires", [])

    def all_required(self) -> "List[Transmogrifier]":
        """Returns a list of zero of more other Transmogrifier objects that this
        Transmogrifier requires, either directly or transitively.
        """
        tlist = []
        for req in self.required:
            tlist += [req] + req.all_required()

        return tlist

    def is_applicable(self, cluster: Cluster) -> bool:
        """Returns true if this Transmogrifier would apply any changes to the
        given Cluster based on the given arguments, false otherwise.
        """
        return True

    def is_ready(self, cluster: Cluster) -> bool:
        """Returns true if this Transmogrifier is ready to make changes to the
        Cluster, or false if it still needs to wait for other Transmogrifiers to
        make their changes before it has the information needed to apply its own
        changes.
        """
        return True

    @abstractmethod
    def check(self, cluster: Cluster) -> CheckResult:
        """Checks for problems with making the requested changes to the given
        Cluster, and returns a CheckResult with any warnings and errors found.
        """
        pass

    @abstractmethod
    def apply(self, cluster: Cluster):
        """Makes some changes to the given Cluster object."""
        pass

    @abstractmethod
    def description(self, cluster: Cluster) -> ChangeDescription:
        """Returns an object that describes the changes apply() would make to
        the Cluster, if any.
        """
        pass


def opt(*args, **kwargs) -> Dict[str, Dict[str, Any]]:
    """Takes the same function arguments as argparse.add_argument(), and returns
    a dict mapping the (main) option name to the given kwargs. If more than one
    option name is given, the others are added to the kwargs as aliases, which
    must be removed before calling add_argument().

    This is a utility function to make it easier for Transmogrifier subclasses
    to define the options() they need in a familiar syntax:

        def options(self):
            return {
                **opt("--animals", nargs="+", …),
                **opt("--allow-birds", action="store_true", …),
            }
    """

    optname = args[0]
    if args[1:]:
        kwargs["aliases"] = args[1:]

    return {optname: {**kwargs}}


def apply(cluster: Cluster, tlist: List[Transmogrifier]):
    """Applies each of the list of Transmogrifiers to the given Cluster, along
    with any of their dependencies."""

    if not tlist:
        raise ConfigureError(
            "Nothing to do (add options to specify what to change; see --help)"
        )

    check_result = check(cluster, tlist)
    if check_result.errors:
        # XXX: We should figure out how to format this sensibly.
        raise TransmogrifierError(f"Preconditions failed: {check_result}")
    if check_result.warnings:
        print(check_result)

    # Expand tlist to include dependencies, then prune anything that's not
    # applicable to the cluster.
    tlist = reduce(add, [t.all_required() + [t] for t in tlist], [])
    ts = deque([t for t in tlist if t.is_applicable(cluster)])

    # We take the first item in the queue and either apply it if it's ready, or
    # move it to the end of the queue to be retried later, and keep going until
    # we run out of Transmogrifiers to apply.

    while ts:
        t = ts.popleft()
        if t.is_ready(cluster):
            t.apply(cluster)
        else:
            ts.append(t)

        # If we end up with a queue where no Transmogrifier is ready, it means
        # there's a bug somewhere in one of the is_ready() tests.

        if ts and not any(t.is_ready(cluster) for t in ts):
            raise TransmogrifierError(
                "Internal error: no Transmogrifier ready to apply"
            )


def describe(cluster: Cluster, tlist: List[Transmogrifier]) -> ChangeDescription:
    """Returns a composite description of what changes the list of
    Transmogrifiers would make to the given Cluster.
    """
    items = []

    for t in tlist:
        if not t.is_applicable(cluster):
            continue

        # Prepend the descriptions from any required objects to the items of
        # this object's description.

        desc = t.description(cluster)
        if t.required:
            desc._items = [describe(cluster, t.required)] + desc._items

        items.append(desc)

    return ChangeDescription(items=items)


def check(cluster: Cluster, tlist: List[Transmogrifier]) -> CheckResult:
    """Returns a CheckResult containing warnings and errors accumulated by
    running checks from the given Transmogrifiers on the Cluster.
    """

    result = CheckResult()

    for t in tlist:
        if not t.is_applicable(cluster):
            continue

        result.absorb(check(cluster, t.required))
        result.absorb(t.check(cluster))

    return result
