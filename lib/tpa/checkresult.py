#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

from typing import List


class CheckResult:
    """Represents the results of running checks from a list of Transmogrifiers
    against a Cluster, comprising a list of zero or more errors and warnings.
    """

    def __init__(self):
        self._warnings: List[str] = []
        self._errors: List[str] = []

    def warning(self, msg: str):
        """Record the given msg as a warning."""
        self._warnings.append(msg)

    @property
    def warnings(self) -> List[str]:
        """Return a list of warnings."""
        return self._warnings

    def error(self, msg: str):
        """Record the given msg as an error."""
        self._errors.append(msg)

    @property
    def errors(self) -> List[str]:
        """Return a list of error messages."""
        return self._errors

    def absorb(self, other: "CheckResult"):
        """Takes the warnings and errors from the given CheckResult and appends
        them to this object's lists of warnings and errors.
        """
        self._warnings += other.warnings
        self._errors += other.errors

    def __str__(self) -> str:
        s = ""

        if self.warnings:
            s += "Warnings:\n"
            s += "\n".join([f"* {w}" for w in self.warnings])
            if self.errors:
                s += "\n"

        if self.errors:
            s += "Errors:\n"
            s += "\n".join([f"* {e}" for e in self.errors])

        return s or "Nothing to report"
