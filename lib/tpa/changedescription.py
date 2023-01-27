#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

from textwrap import wrap, indent
from typing import List, Optional, Any


class ChangeDescription:
    """Represents a list of changes to a Cluster.

    A change description comprises an optional title (e.g., "Transmogrify eel
    to giant bug") and zero or more individual items, each one describing some
    change (e.g., "Set number of wings to 42"). Each item may be a string or a
    ChangeDescription.

    For example,

        a = ChangeDescription(items=["x","y","z"])
        b = ChangeDescription(title="First subtask", items=["task",a])
        c = ChangeDescription(title="Top-level task", items=[b])

    would result in str(c) being

        * Top-level task
          * First subtask
            * task
            * x
            * y
            * z

    If a ChangeDescription has no title, its items become siblings to the items
    of any ChangeDescription that includes it."""

    def __init__(self, title: Optional[str] = None, items: Optional[List[Any]] = None):
        self._title = title
        self._items = items or ["No changes"]

    def __str__(self) -> str:
        """Returns a human-readable description of a set of changes."""

        level = 0
        lines = []

        # If there's a title, we need to add a level of indentation to
        # everything that follows.
        if self._title:
            lines += wrap(self._title, initial_indent="* ", subsequent_indent="  ")
            level += 1

        # If an item is a string, we wrap it to a reasonable width, indent it as
        # required, and add the resulting lines to the output. Otherwise, if the
        # item is itself a ChangeDescription, we can just indent its output as a
        # whole. (Note: we don't try to re-wrap long lines in the output even if
        # we're indenting them multiple times. Write crisp descriptions!)
        for i in self._items:
            s = str(i)
            if isinstance(i, ChangeDescription):
                lines += indent(s, prefix=level*"  ").splitlines()
            else:
                lines += wrap(
                    s,
                    width=65,
                    initial_indent=level * "  " + "* ",
                    subsequent_indent=(level + 1) * "  ",
                )

        return "\n".join(lines)
