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


class FilterModule:
    def filters(self):
        return {
            "selects": selects,
            "permits": permits,
            "strict_selects": strict_selects,
        }
