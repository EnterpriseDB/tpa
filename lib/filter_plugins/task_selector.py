#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.


def selects(selector, *tags) -> bool:
    """
    The selector is a dict with the keys "include" and "exclude", each
    containing a list of strings. Returns true if for every given tag,
    it is both (a) not explicitly excluded and (b) included, either
    explicitly or by the include list being empty.

    """

    exclude = selector.get("exclude", [])
    include = selector.get("include", [])
    if set(tags).intersection(exclude):
        return False
    if not include or set(tags).intersection(include):
        return True
    return False


def strict_selects(selector, *tags) -> bool:
    """The selector is a dict with the keys "include" and "exclude", each.

    containing a list of strings. Returns true if for every given tag,
    it is both (a) not explicitly excluded and (b) explicitly included.

    """
    exclude = selector.get("exclude", [])
    include = selector.get("include", [])
    if set(tags).intersection(exclude):
        return False
    if set(tags).intersection(include):
        return True
    return False


def permits(selector, *tags) -> bool:
    """The selector is a dict with the key "exclude", containing a list of
    strings. Returns true if for every given tag, it is not in the exclude
    list, else returns false.
    """

    exclude = selector.get("exclude", [])
    if set(tags).intersection(exclude):
        return False
    return True


def opts_in(selector, *tags) -> bool:
    """The selector is a dict with the keys "opt_in" and "exclude", each
    containing a list of strings. Returns true if for every given tag, it
    is both (a) not explicitly excluded and (b) explicitly opted in to.
    containing a list of strings. Returns true if both:
        - every given tag is not in the exclude list
        - at least one given tag is in the opt_in list

    Use this filter to gate tasks that should run only when the operator
    has opted in via `opt_in_tasks`. Unlike `strict_selects`, this
    filter does not consume the `included_tasks` whitelist, so a task
    gated by `opts_in` can be enabled without implicitly excluding
    every other task in the deploy.

    """

    exclude = selector.get("exclude", [])
    opt_in = selector.get("opt_in", [])
    if set(tags).intersection(exclude):
        return False
    if set(tags).intersection(opt_in):
        return True
    return False


class FilterModule:
    def filters(self):
        return {
            "selects": selects,
            "permits": permits,
            "strict_selects": strict_selects,
            "opts_in": opts_in,
        }
