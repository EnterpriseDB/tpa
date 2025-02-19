#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

from typing import Dict, List, Any
import fnmatch as fnm

def fnmatch(string: str, pattern: str) -> bool:
    """Given a package version as returned by apt-cache, return True iff it
    matches the package_spec
    """
    if (fnm.fnmatch(string, pattern)):
        return True
    return False

class FilterModule(object):
    def filters(self):
        return {
            "fnmatch": fnmatch,
        }
